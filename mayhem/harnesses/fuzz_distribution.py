#!/usr/bin/env python3
"""ansible.module_utils.facts.system.distribution.DistributionFiles: the distribution-file parsers
(os-release, lsb-release, *-release vendor files) that fact gathering runs over files on managed
hosts. The first byte picks the parser; the rest is the file content."""
import sys
import atheris

with atheris.instrument_imports(include=["ansible"]):
    from ansible.module_utils.facts.system.distribution import DistributionFiles
    import _common


class _NoBinModule:
    """AnsibleModule stand-in: no helper binaries (dpkg etc.) exist, so no command is ever run."""

    def get_bin_path(self, *args, **kwargs):
        return None

    def run_command(self, *args, **kwargs):
        raise AssertionError("run_command must not be reached when get_bin_path returns None")


DIST = DistributionFiles(_NoBinModule())
PARSERS = sorted(n for n in dir(DIST) if n.startswith("parse_distribution_file_"))


def TestOneInput(data):
    if not data:
        return
    meth = PARSERS[data[0] % len(PARSERS)]
    name = meth[len("parse_distribution_file_"):]
    text = data[1:].decode("utf-8", "replace")
    path = _common.write_input("release", text.encode("utf-8"))
    # Fact gathering pre-seeds these before any parser runs (DistributionFiles.process_dist_files).
    collected = {"distribution_release": "NA", "distribution_version": "NA",
                 "distribution_major_version": "NA", "distribution": "NA"}
    getattr(DIST, meth)(name, text, path, collected)


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
