#!/usr/bin/env python3
"""ansible.plugins.inventory.yaml / toml: the YAML and TOML inventory parsers (group/host trees,
vars, children). Untrusted input: inventory files in repo content. The first byte picks the format."""
import sys
import atheris

with atheris.instrument_imports(include=["ansible"]):
    from ansible.errors import AnsibleError
    from ansible.inventory.data import InventoryData
    from ansible.parsing.dataloader import DataLoader
    from ansible.plugins.inventory import yaml as inv_yaml
    from ansible.plugins.inventory import toml as inv_toml
    import _common


def TestOneInput(data):
    if not data:
        return
    if data[0] & 1:
        path = _common.write_input("hosts.toml", data[1:])
        plugin = inv_toml.InventoryModule()
    else:
        path = _common.write_input("hosts.yml", data[1:])
        plugin = inv_yaml.InventoryModule()
    try:
        plugin.parse(InventoryData(), DataLoader(), path)
    except AnsibleError:
        pass


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
