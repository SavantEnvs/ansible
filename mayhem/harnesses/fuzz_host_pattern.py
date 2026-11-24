#!/usr/bin/env python3
"""Host pattern / address grammar: split_host_pattern, parse_address, expand_hostname_range and
InventoryManager.list_hosts over a fixed in-memory inventory. Untrusted input: --limit / hosts:
patterns and host entries in repo content."""
import sys
import atheris

with atheris.instrument_imports(include=["ansible"]):
    from ansible.errors import AnsibleError
    from ansible.inventory.manager import InventoryManager, split_host_pattern
    from ansible.parsing.dataloader import DataLoader
    from ansible.parsing.utils.addresses import parse_address
    from ansible.plugins.inventory import detect_range, expand_hostname_range

INV_SRC = "web1.example.com,web2.example.com,db1,10.0.0.1,[::1]:22,"


def TestOneInput(data):
    if not data:
        return
    mode = data[0] % 3
    s = data[1:].decode("utf-8", "replace")
    try:
        if mode == 0:
            split_host_pattern(s)
            # A fresh inventory per input: list_hosts caches pattern results.
            InventoryManager(loader=DataLoader(), sources=INV_SRC).list_hosts(s)
        elif mode == 1:
            parse_address(s, allow_ranges=True)
        else:
            if detect_range(s):
                expand_hostname_range(s)
    except AnsibleError:
        pass


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
