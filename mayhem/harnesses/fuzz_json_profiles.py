#!/usr/bin/env python3
"""ansible's JSON serialization profiles (module_utils.common.json get_decoder/get_encoder): tagged
JSON decoding (__ansible_vault, __ansible_unsafe, datatags) and the re-encode round trip.
Untrusted input: module results returned by managed hosts, inventory script output, fact caches."""
import json
import sys
import atheris

with atheris.instrument_imports(include=["ansible"]):
    from ansible.errors import AnsibleError
    from ansible.module_utils.common.json import get_decoder, get_encoder

PROFILES = ["legacy", "inventory_legacy", "cache_persistence", "tagless", "module_legacy_m2c", "module_legacy_c2m",
            "module_modern_m2c", "module_modern_c2m"]
CODECS = []
for _p in PROFILES:
    try:
        CODECS.append((get_decoder(_p), get_encoder(_p)))
    except Exception:  # profile name not present in this ansible version
        pass
assert CODECS, "no JSON profiles resolved"


def TestOneInput(data):
    if not data:
        return
    dec, enc = CODECS[data[0] % len(CODECS)]
    s = data[1:].decode("utf-8", "replace")
    try:
        obj = json.loads(s, cls=dec)
    except (ValueError, AnsibleError):
        return
    try:
        json.dumps(obj, cls=enc)
    except (AnsibleError, TypeError):
        pass


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
