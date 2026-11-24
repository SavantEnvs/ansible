#!/usr/bin/env python3
"""ansible.config.manager.ConfigManager: ansible.cfg INI parsing and per-setting type coercion
(ensure_type: bool/int/list/pathlist/dict/...). Untrusted input: an ansible.cfg shipped in a repo
(ansible reads ./ansible.cfg from the working directory)."""
import sys
import atheris

with atheris.instrument_imports(include=["ansible"]):
    from ansible.errors import AnsibleError
    from ansible.config.manager import ConfigManager
    import _common

# Every setting with an ini entry; evaluated against each input's config file.
_NAMES = None


def TestOneInput(data):
    global _NAMES
    path = _common.write_input("ansible.cfg", data)
    try:
        cm = ConfigManager(conf_file=path)
        if _NAMES is None:
            _NAMES = sorted(cm.get_configuration_definitions().keys())
        for name in _NAMES:
            try:
                cm.get_config_value(name)
            except AnsibleError:
                pass
    except AnsibleError:
        pass


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
