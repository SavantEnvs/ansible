#!/usr/bin/env python3
"""ansible.parsing.utils.yaml.from_yaml: ansible's tagged YAML loader (!vault, !unsafe, origin tags)
and its JSON fast path. Untrusted input: playbooks, vars files, inventories in repo content."""
import sys
import atheris

with atheris.instrument_imports(include=["ansible"]):
    from ansible.errors import AnsibleError
    from ansible.parsing.utils.yaml import from_yaml
    from ansible.parsing.dataloader import DataLoader


def TestOneInput(data):
    if not data:
        return
    mode = data[0] % 3
    s = data[1:].decode("utf-8", "replace")
    try:
        if mode == 0:
            from_yaml(s)
        elif mode == 1:
            from_yaml(s, json_only=True)
        else:
            DataLoader().load(s)
    except AnsibleError:
        pass


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
