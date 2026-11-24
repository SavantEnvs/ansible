#!/usr/bin/env python3
"""ansible-galaxy collection artifact readers: _get_meta_from_tar (MANIFEST.json -> collection_info),
_get_json_from_tar_file / _get_tar_file_hash (FILES.json, as verify_collection reads it) and
_get_runtime_from_tar (meta/runtime.yml). Untrusted input: collection tarballs from Galaxy servers,
URLs or requirements files.

Input layout: data[0] selects the mode, data[1:] is the payload.
  data[0] == 0   the payload IS the artifact file (any container: gzip/bz2/xz/plain tar), so the
                 container-level errors stay reachable; runs the meta + FILES.json readers. Only 1/256
                 of the selector space: almost any mutation of a gzip stream ends in gzip's EOFError,
                 a process restart per input, so this mode must not dominate the run.
  data[0] != 0   the payload is split on NUL into up to three member bodies, MANIFEST.json,
                 FILES.json and meta/runtime.yml (an absent piece = an absent member), packed into an
                 uncompressed tar (tarfile.open(mode='r') reads plain tar, as for any artifact) so the
                 mutations land in what ansible parses instead of breaking the gzip stream;
                 (data[0]-1) % 3: 0 -> _get_meta_from_tar, 1 -> FILES.json readers, 2 -> _get_runtime_from_tar.
"""
import io
import sys
import tarfile
import atheris
import yaml

with atheris.instrument_imports(include=["ansible"]):
    from ansible.errors import AnsibleError
    from ansible.galaxy.collection.concrete_artifact_manager import (
        _get_meta_from_tar, _get_runtime_from_tar)
    from ansible.galaxy.collection import _get_json_from_tar_file, _get_tar_file_hash
    import _common

MEMBERS = ("MANIFEST.json", "FILES.json", "meta/runtime.yml")


def build_tar(payload):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w", format=tarfile.GNU_FORMAT) as tar:
        for name, body in zip(MEMBERS, payload.split(b"\0", len(MEMBERS) - 1)):
            info = tarfile.TarInfo(name)
            info.size = len(body)
            info.mtime = 0
            tar.addfile(info, io.BytesIO(body))
    return buf.getvalue()


def read_meta(b_path):
    try:
        _get_meta_from_tar(b_path)
    except (AnsibleError, tarfile.TarError):
        pass


def read_files_json(b_path):
    try:
        _get_tar_file_hash(b_path, "FILES.json")
        # Returns json.loads() of the member; ValueError (JSONDecodeError) is json.loads' documented
        # result for a body that is not JSON, not a defect in the reader.
        _get_json_from_tar_file(b_path, "FILES.json")
    except (AnsibleError, tarfile.TarError, ValueError):
        pass


def read_runtime(b_path):
    # @functools.cache keyed on the path: the scratch path is fixed, so reset it per input.
    _get_runtime_from_tar.cache_clear()
    try:
        _get_runtime_from_tar(b_path)
    except yaml.YAMLError:
        # yaml_load (yaml.load, SafeLoader) documents YAMLError for text that is not YAML.
        pass


def TestOneInput(data):
    if not data:
        return -1
    selector, payload = data[0], data[1:]
    if selector == 0:
        b_path = _common.write_input("collection.tar.gz", payload).encode()
        read_meta(b_path)
        read_files_json(b_path)
        return 0
    b_path = _common.write_input("collection.tar", build_tar(payload)).encode()
    (read_meta, read_files_json, read_runtime)[(selector - 1) % 3](b_path)
    return 0


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
