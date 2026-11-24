#!/usr/bin/env python3
"""ansible.parsing.plugin_docs: extraction of DOCUMENTATION/EXAMPLES/RETURN from plugin sources
(Python AST walk) and sidecar YAML docs. Untrusted input: plugins inside collections/roles that
ansible-doc / the loader read. The first byte picks .py vs .yml."""
import sys
import atheris

with atheris.instrument_imports(include=["ansible"]):
    from ansible.errors import AnsibleError
    from ansible.parsing.plugin_docs import read_docstring_from_python_file, read_docstring_from_yaml_file
    import _common


def TestOneInput(data):
    if not data:
        return
    try:
        if data[0] & 1:
            read_docstring_from_yaml_file(_common.write_input("plugin.yml", data[1:]), verbose=False, ignore_errors=False)
        else:
            read_docstring_from_python_file(_common.write_input("plugin.py", data[1:]), verbose=False, ignore_errors=False)
    except (AnsibleError, SyntaxError, ValueError, RecursionError):
        # SyntaxError/ValueError/RecursionError: ast.parse's documented rejections of invalid or too-deep source.
        pass


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
