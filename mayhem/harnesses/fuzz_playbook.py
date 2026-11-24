#!/usr/bin/env python3
"""ansible.playbook.Playbook.load: playbook object loading (plays, blocks, tasks, handlers, roles
lists, field attribute validation, module-args parsing). Untrusted input: playbook files."""
import sys
import atheris

with atheris.instrument_imports(include=["ansible"]):
    from ansible.errors import AnsibleError
    from ansible.parsing.dataloader import DataLoader
    from ansible.playbook import Playbook
    from ansible.vars.manager import VariableManager
    import _common


def TestOneInput(data):
    path = _common.write_input("play.yml", data)
    loader = DataLoader()
    try:
        pb = Playbook.load(path, variable_manager=VariableManager(loader=loader), loader=loader)
        for play in pb.get_plays():
            play.compile()
            play.get_vars()
            play.get_roles()
    except AnsibleError:
        pass


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
