#!/usr/bin/env python3
"""ansible.plugins.inventory.ini: the INI inventory parser (groups, :vars/:children sections, host
definitions, host ranges, addresses). Untrusted input: inventory files in repo content."""
import sys
import atheris

with atheris.instrument_imports(include=["ansible"]):
    from ansible.errors import AnsibleError
    from ansible.inventory.data import InventoryData
    from ansible.parsing.dataloader import DataLoader
    from ansible.plugins.inventory.ini import InventoryModule
    import _common


def TestOneInput(data):
    path = _common.write_input("hosts.ini", data)
    try:
        InventoryModule().parse(InventoryData(), DataLoader(), path)
    except AnsibleError:
        pass


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
