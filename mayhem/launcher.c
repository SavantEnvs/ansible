/*
 * launcher.c — a tiny ELF wrapper that runs the Atheris (Python) fuzz harness.
 *
 * Mayhem requires the target `cmd:` to be an ELF (it rejects shell/script
 * wrappers) and our gate checks each target binary for DWARF < 4 debug info.
 * An Atheris harness is a Python script, so we compile this launcher (with
 * $DEBUG_FLAGS, i.e. -gdwarf-3) to an ELF that execs the interpreter on the
 * harness and forwards every libFuzzer argument.
 *
 * The harness path and the python interpreter are baked in at compile time via
 * -DHARNESS=... and -DPYTHON=... so the binary is self-contained.
 *
 * ansible creates its local temp dir (DEFAULT_LOCAL_TMP, default ~/.ansible/tmp) at config load.
 * $HOME may be unwritable for the user Mayhem runs as, and a fixed shared path breaks when another
 * uid created it first, so each process gets a fresh private dir under $TMPDIR (default /tmp)
 * unless the caller already set ANSIBLE_LOCAL_TEMP.
 */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>

#ifndef PYTHON
#define PYTHON "python3"
#endif
#ifndef HARNESS
#define HARNESS "/mayhem/mayhem/fuzz_diff.py"
#endif

int main(int argc, char **argv) {
    if (!getenv("ANSIBLE_LOCAL_TEMP")) {
        const char *tmp = getenv("TMPDIR");
        char dir[4096];
        snprintf(dir, sizeof dir, "%s/ansible-fuzz-XXXXXX", (tmp && *tmp) ? tmp : "/tmp");
        if (mkdtemp(dir)) {
            setenv("ANSIBLE_LOCAL_TEMP", dir, 1);
        }
    }
    /* argv: PYTHON HARNESS <forwarded args...> NULL */
    char **a = (char **)calloc((size_t)argc + 2, sizeof(char *));
    if (!a) {
        perror("calloc");
        return 1;
    }
    int n = 0;
    a[n++] = (char *)PYTHON;
    a[n++] = (char *)HARNESS;
    for (int i = 1; i < argc; i++) {
        a[n++] = argv[i];
    }
    a[n] = NULL;
    execvp(PYTHON, a);
    /* only reached if exec failed */
    perror("execvp " PYTHON);
    return 127;
}
