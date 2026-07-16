from __future__ import annotations

import argparse
import hashlib
import json
import secrets
from pathlib import Path


try:
    from Crypto.Cipher import AES
except ImportError as exc:  # pragma: no cover - exercised by audit script.
    AES = None
    AES_IMPORT_ERROR = exc
else:
    AES_IMPORT_ERROR = None


class SecurePayloadError(ValueError):
    pass


def derive_aes256_key(secret: bytes | str, context: bytes | str = b"ETHEGAN-AEAD-v1") -> bytes:
    if isinstance(secret, str):
        secret = secret.encode("utf-8")
    if isinstance(context, str):
        context = context.encode("utf-8")
    return hashlib.sha256(context + b"\0" + secret).digest()


def encrypt_payload_aes_gcm(
    payload: bytes,
    key: bytes,
    associated_data: bytes = b"",
    nonce: bytes | None = None,
) -> bytes:
    if AES is None:
        raise SecurePayloadError(f"PyCryptodome AES is unavailable: {AES_IMPORT_ERROR}")
    if len(key) != 32:
        raise SecurePayloadError("AES-GCM requires a 32-byte AES-256 key")
    nonce = secrets.token_bytes(12) if nonce is None else bytes(nonce)
    if len(nonce) != 12:
        raise SecurePayloadError("AES-GCM nonce must be 12 bytes")
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    if associated_data:
        cipher.update(associated_data)
    ciphertext, tag = cipher.encrypt_and_digest(payload)
    return nonce + tag + ciphertext


def decrypt_payload_aes_gcm(
    packet: bytes,
    key: bytes,
    associated_data: bytes = b"",
) -> bytes:
    if AES is None:
        raise SecurePayloadError(f"PyCryptodome AES is unavailable: {AES_IMPORT_ERROR}")
    if len(key) != 32:
        raise SecurePayloadError("AES-GCM requires a 32-byte AES-256 key")
    if len(packet) < 28:
        raise SecurePayloadError("encrypted packet is shorter than nonce+tag")
    nonce = packet[:12]
    tag = packet[12:28]
    ciphertext = packet[28:]
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    if associated_data:
        cipher.update(associated_data)
    try:
        return cipher.decrypt_and_verify(ciphertext, tag)
    except ValueError as exc:
        raise SecurePayloadError("AES-GCM authentication failed") from exc


def self_test() -> dict[str, object]:
    payload = b"ETHEGAN confidential payload test"
    aad = b"payload-bpp=0.25|packet-v3"
    key = derive_aes256_key("correct shared secret")
    wrong_key = derive_aes256_key("wrong shared secret")
    encrypted = encrypt_payload_aes_gcm(payload, key, associated_data=aad, nonce=b"\x00" * 12)
    recovered = decrypt_payload_aes_gcm(encrypted, key, associated_data=aad)
    wrong_key_failed = False
    wrong_aad_failed = False
    try:
        decrypt_payload_aes_gcm(encrypted, wrong_key, associated_data=aad)
    except SecurePayloadError:
        wrong_key_failed = True
    try:
        decrypt_payload_aes_gcm(encrypted, key, associated_data=b"wrong aad")
    except SecurePayloadError:
        wrong_aad_failed = True
    return {
        "aead": "AES-256-GCM",
        "provider": "pycryptodome",
        "payload_bytes": len(payload),
        "encrypted_bytes": len(encrypted),
        "correct_key_recovers_plaintext": recovered == payload,
        "wrong_key_authentication_fails": wrong_key_failed,
        "wrong_associated_data_authentication_fails": wrong_aad_failed,
        "ready_for_pre_packet_encryption": recovered == payload and wrong_key_failed and wrong_aad_failed,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="ETHEGAN AES-GCM payload-confidentiality self-test.")
    parser.add_argument("--out-json")
    args = parser.parse_args()
    result = self_test()
    if args.out_json:
        out = Path(args.out_json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ready_for_pre_packet_encryption"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
