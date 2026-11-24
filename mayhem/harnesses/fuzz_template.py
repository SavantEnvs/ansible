#!/usr/bin/env python3
"""ansible.template.Templar: the Jinja2-based templating engine (template / evaluate_expression /
evaluate_conditional) with ansible's filters, tests and lazy containers. Untrusted input: template
strings in playbooks, vars and inventories.

Hermeticity: lookup plugins are allow-listed. Lookups such as pipe/file/url/env/password run
commands, read files or hit the network; the harness replaces lookup_loader.get so only pure,
in-memory lookups resolve (others fail as "plugin not found", an AnsibleError).
"""
import sys
import atheris

with atheris.instrument_imports(include=["ansible"]):
    from ansible.errors import AnsibleError
    from ansible.template import Templar, trust_as_template
    from ansible.plugins.loader import lookup_loader, filter_loader, test_loader
    import ansible.plugins.filter.core
    import ansible.plugins.filter.mathstuff
    import ansible.plugins.filter.urlsplit
    import ansible.plugins.filter.urls
    import ansible.plugins.test.core
    import ansible.plugins.lookup.items
    import ansible.plugins.lookup.list
    import ansible.plugins.lookup.dict
    import ansible.plugins.lookup.sequence
    import ansible.plugins.lookup.together
    import ansible.plugins.lookup.nested
    import ansible.plugins.lookup.indexed_items
    import ansible.plugins.lookup.subelements

_ALLOWED_LOOKUPS = {"items", "list", "dict", "sequence", "together", "nested", "indexed_items", "subelements"}
_orig_get = lookup_loader.get


def _safe_get(name, *args, **kwargs):
    short = str(name).rsplit(".", 1)[-1]
    if short not in _ALLOWED_LOOKUPS:
        return None
    return _orig_get(short, *args, **kwargs)


lookup_loader.get = _safe_get

# Fixed, read-only variable set (rebuilt per input so templating can't mutate shared state).
def _vars():
    return {
        "a": 1, "b": "two", "c": [1, 2, 3], "d": {"k": "v", "n": {"x": [4, 5]}},
        "t": True, "f": 3.5, "s": "Hello World", "empty": "",
    }


def TestOneInput(data):
    if not data:
        return
    mode = data[0] % 3
    s = data[1:].decode("utf-8", "replace")
    templar = Templar(variables=_vars())
    try:
        if mode == 0:
            templar.template(trust_as_template(s))
        elif mode == 1:
            templar.evaluate_expression(trust_as_template(s))
        else:
            templar.evaluate_conditional(trust_as_template(s))
    except AnsibleError:
        pass


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
