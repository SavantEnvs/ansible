#!/usr/bin/env python3
"""ansible.parsing.vault: vault envelope parsing (header, vault-id, hex payload, HMAC) and AES256
decryption. Untrusted input: vault files / !vault values in repo content."""
import sys
import atheris

with atheris.instrument_imports(include=["ansible"]):
    from ansible.errors import AnsibleError
    from ansible.parsing.vault import VaultLib, VaultSecret, is_encrypted, parse_vaulttext_envelope

_VAULT = VaultLib([("default", VaultSecret(b"fuzzpassword"))])


def TestOneInput(data):
    try:
        is_encrypted(data)
        parse_vaulttext_envelope(data)
    except AnsibleError:
        pass
    try:
        _VAULT.decrypt(data)
    except AnsibleError:
        pass


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
