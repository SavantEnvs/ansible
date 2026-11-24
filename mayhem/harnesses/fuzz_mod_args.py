#!/usr/bin/env python3
"""ansible.parsing.mod_args.ModuleArgsParser + splitter.parse_kv: normalization of a task's action
(old-style 'module k=v' strings, action/local_action/args dicts) and the jinja-aware key=value
tokenizer. Untrusted input: task definitions in playbooks/roles. One action key per input."""
import sys
import atheris

with atheris.instrument_imports(include=["ansible"]):
    from ansible.errors import AnsibleError
    from ansible.parsing.mod_args import ModuleArgsParser
    from ansible.parsing.splitter import parse_kv


def TestOneInput(data):
    if not data:
        return
    mode = data[0] % 5
    s = data[1:].decode("utf-8", "replace")
    if not s.strip():
        # A blank action string raises an uncaught IndexError in mod_args._split_module_string
        # (a known upstream bug, reproduced by the fuzz_task target). Every input starting with it
        # would end the run at the first exec, so blank strings go to parse_kv only.
        mode = 4
    try:
        if mode == 0:
            ModuleArgsParser({"action": s}).parse()
        elif mode == 1:
            ModuleArgsParser({"local_action": s}).parse()
        elif mode == 2:
            ModuleArgsParser({"shell": s}).parse()
        elif mode == 3:
            ModuleArgsParser({"ansible.builtin.copy": s}).parse()
        else:
            parse_kv(s, check_raw=True)
    except AnsibleError:
        pass


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
