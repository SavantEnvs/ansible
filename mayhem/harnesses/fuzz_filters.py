#!/usr/bin/env python3
"""ansible's builtin filter plugins applied to untrusted DATA: the input is a variable value (e.g. a
registered module result or remote fact), piped through one filter picked by the first byte; the
template text itself is fixed and trusted. Covers core (b64decode, from_json/yaml, regex_*, to_uuid,
comment, split, ...), mathstuff (human_to_bytes, unique, ...), urlsplit and urls filters."""
import sys
import atheris

with atheris.instrument_imports(include=["ansible"]):
    from ansible.errors import AnsibleError
    from ansible.template import Templar, trust_as_template
    import ansible.plugins.filter.core
    import ansible.plugins.filter.mathstuff
    import ansible.plugins.filter.urlsplit
    import ansible.plugins.filter.urls

# `x` is the fuzzed value, `y` a second fuzzed string (pattern, delimiter, seed).
EXPRS = [
    "x | b64decode", "x | from_json", "x | from_yaml", "x | from_yaml_all | list", "x | to_uuid",
    "x | regex_escape", "x | regex_search(y)", "x | regex_replace(y, 'Z')", "x | regex_findall(y)",
    "x | urldecode", "x | urlsplit", "x | urlsplit('query')", "x | quote", "x | comment",
    "x | comment('c', decoration=y)", "x | human_to_bytes", "x | human_to_bytes(isbits=true)",
    "x | split(y)", "x | bool", "x | to_nice_yaml", "x | to_json | from_json", "x | basename",
    "x | splitext", "x | win_splitdrive", "x | normpath", "x | list | unique", "x | type_debug",
    "x | ternary(y, 'n')", "x | strftime(0)", "x | to_datetime", "x | to_datetime(y)",
    "x | checksum", "x | hash('sha1')", "x | password_hash('sha512', 'saltsalt', rounds=1000)",
    "x | from_json | dict2items", "x | from_yaml | items2dict", "x | from_json | combine({'a': 1}, recursive=true)",
    "x | extract({'a': 1})", "x | from_json | flatten", "x | split(',') | map('int') | sum",
    "x | log", "x | root", "x | random(seed=y)", "x | shuffle(seed=y) | join",
]


def TestOneInput(data):
    fdp = atheris.FuzzedDataProvider(data)
    expr = EXPRS[fdp.ConsumeIntInRange(0, len(EXPRS) - 1)]
    y = fdp.ConsumeUnicodeNoSurrogates(16)
    x = fdp.ConsumeUnicodeNoSurrogates(4096)
    try:
        Templar(variables={"x": x, "y": y}).evaluate_expression(trust_as_template(expr))
    except AnsibleError:
        pass


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
