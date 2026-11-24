#!/usr/bin/env python3
"""ansible.module_utils.common.arg_spec.ArgumentSpecValidator: module-side argument validation and
type coercion (check_type_* incl. the key=value dict parser, human_to_bytes). Untrusted input:
module arguments (JSON) delivered to managed hosts."""
import json
import sys
import atheris

with atheris.instrument_imports(include=["ansible"]):
    from ansible.module_utils.common.arg_spec import ArgumentSpecValidator
    from ansible.module_utils.common import validation

SPEC = {
    "s": {"type": "str"}, "i": {"type": "int"}, "fl": {"type": "float"}, "b": {"type": "bool"},
    "l": {"type": "list", "elements": "int"}, "d": {"type": "dict"}, "p": {"type": "path"},
    "raw": {"type": "raw"}, "j": {"type": "jsonarg"}, "by": {"type": "bytes"}, "bi": {"type": "bits"},
    "c": {"type": "str", "choices": ["a", "b", "c"], "aliases": ["cc"]},
    "dflt": {"type": "int", "default": 5},
    "sub": {"type": "dict", "options": {"x": {"type": "int", "required": True}, "y": {"type": "list", "elements": "str"}},
            "mutually_exclusive": [["x", "y"]]},
    "subl": {"type": "list", "elements": "dict", "options": {"n": {"type": "str"}, "v": {"type": "float"}}},
}
VALIDATOR = ArgumentSpecValidator(SPEC, mutually_exclusive=[["s", "raw"]], required_if=[["b", True, ["i"]]],
                                  required_together=[["fl", "by"]])


def TestOneInput(data):
    if not data:
        return
    s = data[1:].decode("utf-8", "replace")
    if data[0] & 1:
        try:
            validation.check_type_dict(s)
        except (TypeError, ValueError):
            pass
        return
    try:
        params = json.loads(s)
    except ValueError:
        return
    if not isinstance(params, dict):
        return
    VALIDATOR.validate(params)


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
