#!/usr/bin/env bash
#
# mayhem/build.sh — build the ansible-core Atheris fuzz targets + standalone reproducers and the
# pytest runner for the unit-test oracle. Runs in the commit image as `mayhem` in /mayhem.
#
# ansible-core is pure Python (src layout: lib/ansible). It is NOT pip-installed: lib/ is put on
# PYTHONPATH so a PATCH agent's edits under lib/ansible take effect with no reinstall.
# Re-runnable + air-gapped (SPEC §6.2 item 9 / §6.5):
#   1. the first (online) build fills a wheelhouse at /opt/toolchains/python/wheelhouse;
#   2. deps are installed OFFLINE (pip --no-index --find-links) into /opt/toolchains/python/site;
#   both steps are skipped when already done, so a re-run never needs the network.
# Each target is a compiled ELF launcher (DWARF 3 via $DEBUG_FLAGS) that execs python3 on the
# harness; Atheris instruments ansible's Python at import and links libFuzzer itself. Building the
# launcher with $SANITIZER_FLAGS would only instrument the exec wrapper, so it is not used here.
set -euo pipefail

[ -n "${SOURCE_DATE_EPOCH:-}" ] || unset SOURCE_DATE_EPOCH
: "${DEBUG_FLAGS:=-g -gdwarf-3}"
: "${CC:=clang}"
: "${MAYHEM_JOBS:=$(nproc)}"
export DEBUG_FLAGS CC MAYHEM_JOBS

SRC="${SRC:-/mayhem}"
cd "$SRC"

PY_PREFIX=/opt/toolchains/python
WHEELHOUSE="$PY_PREFIX/wheelhouse"
SITE="$PY_PREFIX/site"
mkdir -p "$WHEELHOUSE" "$SITE"
PY="$(command -v python3)"

# Runtime deps of ansible-core (requirements.txt) + the fuzz engine + the unit-test runner deps
# (test/units/requirements.txt: passlib/bcrypt/pexpect; pywinrm is only for winrm tests, not run).
PKGS=(atheris==3.1.0 "jinja2>=3.1.0" "PyYAML>=5.1" cryptography packaging "resolvelib>=0.8.0,<2.0.0"
      pytest pytest-mock passlib "bcrypt<5" pexpect)

if ls "$WHEELHOUSE"/atheris-*.whl >/dev/null 2>&1; then
  echo ">> wheelhouse already populated — reusing $WHEELHOUSE"
else
  echo ">> populating wheelhouse (online) at $WHEELHOUSE"
  "$PY" -m pip download --only-binary=:all: --dest "$WHEELHOUSE" "${PKGS[@]}"
fi

if [ -f "$SITE/.installed" ]; then
  echo ">> deps already installed in $SITE — skipping"
else
  "$PY" -m pip install --no-index --find-links="$WHEELHOUSE" --target "$SITE" "${PKGS[@]}"
  touch "$SITE/.installed"
fi

export PYTHONPATH="$SITE:$SRC/lib"
"$PY" -c 'import atheris, jinja2, yaml, cryptography, resolvelib, pytest; import ansible.template, ansible.playbook; print("imports OK")'

TARGETS=(fuzz_parse fuzz_task fuzz_encrypt fuzz_yaml fuzz_template fuzz_vault fuzz_inventory_ini
         fuzz_inventory_yaml fuzz_playbook fuzz_argspec fuzz_galaxy_requirement fuzz_json_profiles
         fuzz_host_pattern fuzz_config fuzz_mod_args fuzz_plugin_docs fuzz_collection_tar
         fuzz_filters fuzz_distribution)
for t in "${TARGETS[@]}"; do
  harness="$SRC/mayhem/harnesses/$t.py"
  [ -f "$harness" ] || { echo "missing $harness" >&2; exit 1; }
  # Fuzz target and its run-once reproducer (libFuzzer runs a file argument once, no loop).
  $CC $DEBUG_FLAGS -DPYTHON="\"$PY\"" -DHARNESS="\"$harness\"" "$SRC/mayhem/launcher.c" -o "$SRC/$t"
  $CC $DEBUG_FLAGS -DPYTHON="\"$PY\"" -DHARNESS="\"$harness\"" "$SRC/mayhem/launcher.c" -o "$SRC/$t-standalone"
done

# The unit-test oracle runs through this NON-system ELF so the sabotage check bites.
$CC $DEBUG_FLAGS -DPYTHON="\"$PY\"" "$SRC/mayhem/run_tests.c" -o "$SRC/ansible_run_tests"
echo ">> build.sh complete"
