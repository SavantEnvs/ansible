#!/usr/bin/env python3
"""ansible-galaxy requirement parsing: collection requirement strings (Requirement.from_string),
role specs (RoleRequirement.role_yaml_parse / repo_url_to_role_name) and SemanticVersion.
Untrusted input: requirements.yml / CLI requirement strings from repo content."""
import sys
import atheris
# Import the shared infrastructure (config/constants, templating, plugin loader, jinja2, PyYAML) UNinstrumented
# first: instrumenting it under instrument_imports() pushed startup past Mayhem's smoke-test timeout
# (0 edges, "timed out when printing options"). Only the modules imported below are instrumented.
import jinja2, yaml  # noqa: E401,F401
import ansible.constants, ansible.template, ansible.plugins.loader, ansible.module_utils.basic  # noqa: E401,F401

with atheris.instrument_imports(include=["ansible"]):
    from ansible.errors import AnsibleError
    from ansible.galaxy.dependency_resolution.dataclasses import Requirement
    from ansible.playbook.role.requirement import RoleRequirement
    from ansible.utils.version import SemanticVersion


class _NoArtifacts:
    """Stand-in for ConcreteArtifactsManager. Requirement strings naming a url/file/dir/git source
    make from_requirement_dict ask the artifacts manager for the collection's FQCN, which downloads,
    clones or opens the artifact; this harness fuzzes the requirement *parsing* only, so every
    artifact lookup is refused the way a missing artifact is (AnsibleError)."""

    def __getattr__(self, name):
        def _refuse(*args, **kwargs):
            raise AnsibleError("artifact access disabled in the fuzz harness")
        return _refuse


_ART = _NoArtifacts()


def TestOneInput(data):
    if not data:
        return
    mode = data[0] % 3
    s = data[1:].decode("utf-8", "replace")
    try:
        if mode == 0:
            Requirement.from_string(s, _ART, None)
        elif mode == 1:
            RoleRequirement.role_yaml_parse(s)
            RoleRequirement.repo_url_to_role_name(s)
        elif s:
            # SemanticVersion('') is the unset placeholder (core=None), not a comparable version.
            v = SemanticVersion(s)
            v < SemanticVersion("1.2.3-beta+abc")
            v == SemanticVersion("0.0.1")
    except (AnsibleError, ValueError):
        pass


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
