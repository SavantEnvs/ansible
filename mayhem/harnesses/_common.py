#!/usr/bin/env python3
"""Shared helpers for the ansible Atheris harnesses (mayhem/harnesses).

Each harness imports ansible under atheris.instrument_imports(include=["ansible"]) so SanCov-style
coverage comes from ansible's own code; third-party libraries (jinja2, yaml, cryptography) stay
uninstrumented, like apt libraries in a C image.
"""
import os
import tempfile

_TMPDIR = None


def scratch_dir():
    """A per-process scratch directory under $TMPDIR (Mayhem mounts the image read-only)."""
    global _TMPDIR
    if _TMPDIR is None:
        _TMPDIR = tempfile.mkdtemp(prefix="ansible-fuzz-", dir=os.environ.get("TMPDIR") or None)
    return _TMPDIR


def write_input(name, data):
    """(Re)write the input to a fixed scratch path; every input overwrites the previous one."""
    path = os.path.join(scratch_dir(), name)
    with open(path, "wb") as f:
        f.write(data)
    return path
