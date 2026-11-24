#!/usr/bin/env bash
#
# mayhem/test.sh — RUN a slice of ansible-core's own unit-test suite (test/units, pytest) covering
# the code the fuzz targets reach: parsing (YAML, vault, splitter, mod_args), templating, inventory
# + inventory plugins, playbook objects, config, galaxy requirements, filters and module_utils
# validation. Emits CTRF; exit 0 iff failed==0. The suite asserts behavior (known inputs ->
# expected values), so a no-op patch fails it. Nothing is built here: build.sh installed pytest
# and compiled the ansible_run_tests ELF wrapper (non-system, so the sabotage check bites).
set -uo pipefail
[ -n "${SOURCE_DATE_EPOCH:-}" ] || unset SOURCE_DATE_EPOCH
: "${MAYHEM_JOBS:=$(nproc)}"
SRC="${SRC:-/mayhem}"
cd "$SRC"
export PYTHONPATH="/opt/toolchains/python/site:$SRC/lib:$SRC/test/lib"
export ANSIBLE_LOCAL_TEMP="${TMPDIR:-/tmp}/ansible-test-local"

# emit_ctrf <tool> <passed> <failed> [skipped] [pending] [other]
emit_ctrf() {
  local tool="$1" passed="$2" failed="$3" skipped="${4:-0}" pending="${5:-0}" other="${6:-0}"
  local tests=$(( passed + failed + skipped + pending + other ))
  cat > "${CTRF_REPORT:-$SRC/ctrf-report.json}" <<JSON
{
  "results": {
    "tool": { "name": "$tool" },
    "summary": {
      "tests": $tests,
      "passed": $passed,
      "failed": $failed,
      "pending": $pending,
      "skipped": $skipped,
      "other": $other
    }
  }
}
JSON
  printf 'CTRF {"results":{"tool":{"name":"%s"},"summary":{"tests":%d,"passed":%d,"failed":%d,"pending":%d,"skipped":%d,"other":%d}}}\n' \
    "$tool" "$tests" "$passed" "$failed" "$pending" "$skipped" "$other"
  [ "$failed" -eq 0 ]
}

RUNNER="$SRC/ansible_run_tests"
if [ ! -x "$RUNNER" ]; then
  echo "test.sh: $RUNNER missing — mayhem/build.sh must build it first" >&2
  emit_ctrf pytest 0 1
  exit 1
fi

TESTS=(
  test/units/parsing
  test/units/template
  test/units/inventory
  test/units/plugins/inventory
  test/units/plugins/filter
  test/units/playbook
  test/units/galaxy/test_role_requirements.py
  test/units/module_utils/common
)

# Two warning-capture tests assume ansible-test's harness setup (they see no captured
# deprecation/warning outside it) and fail on a pristine tree; deselected, not part of the oracle.
DESELECT=(
  --deselect test/units/playbook/test_collectionsearch.py::test_collection_static_warning
  --deselect test/units/module_utils/common/arg_spec/test_module_validate.py::test_module_alias_deprecations_warnings
)

LOG="$(mktemp)"
"$RUNNER" -p no:cacheprovider -o addopts= -q "${DESELECT[@]}" "${TESTS[@]}" 2>&1 | tee "$LOG"
rc=${PIPESTATUS[0]}

line="$(grep -E '^(=+ )?[0-9]+ (passed|failed|error|skipped)' "$LOG" | tail -1)"
get() { echo "$line" | grep -oE "[0-9]+ $1" | grep -oE '^[0-9]+' | head -1; }
passed="$(get passed)";   passed="${passed:-0}"
failed="$(get failed)";   failed="${failed:-0}"
errors="$(get error)";    errors="${errors:-0}"
skipped="$(get skipped)"; skipped="${skipped:-0}"
xfailed="$(get xfailed)"; xfailed="${xfailed:-0}"
rm -f "$LOG"
failed=$(( failed + errors ))
if [ "$(( passed + failed + skipped ))" -eq 0 ]; then
  emit_ctrf pytest 0 1
  exit 1
fi
if [ "$rc" -ne 0 ] && [ "$failed" -eq 0 ]; then failed=1; fi
emit_ctrf pytest "$passed" "$failed" "$(( skipped + xfailed ))"
