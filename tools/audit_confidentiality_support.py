from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ETHEGAN_CODE = REPO_ROOT / "05_artifacts" / "code" / "etehgan"
sys.path.insert(0, str(ETHEGAN_CODE))


def available(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def main() -> int:
    cryptography_available = available("cryptography")
    pycryptodome_available = available("Crypto")
    self_test_result = None
    blockers = []
    if pycryptodome_available:
        from secure_payload import self_test

        self_test_result = self_test()
        if not self_test_result["ready_for_pre_packet_encryption"]:
            blockers.append("AES-GCM self-test failed")
    elif cryptography_available:
        blockers.append("cryptography is present, but ETHEGAN AES-GCM wrapper currently uses pycryptodome")
    else:
        blockers.append("No local AEAD provider found: install pycryptodome or cryptography")

    ready = not blockers
    payload = {
        "aead_supported_locally": ready,
        "providers": {
            "cryptography": cryptography_available,
            "pycryptodome": pycryptodome_available,
        },
        "implemented_mechanism": "AES-256-GCM before ETHEGAN packetization",
        "recommended_mechanism": "AES-GCM or XChaCha20-Poly1305 before ETHEGAN packetization",
        "claim_status": "supported" if ready else "blocked",
        "blockers": blockers,
        "self_test": self_test_result,
        "policy": (
            "Payload confidentiality may be claimed only for payloads encrypted before packetization "
            "with AEAD and rejected on authentication failure."
        ),
    }
    out_json = REPO_ROOT / "05_artifacts" / "results" / "raw" / "confidentiality_support_audit.json"
    out_md = REPO_ROOT / "04_experiments" / "results" / "confidentiality_support_audit_2026-07-16.md"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    out_md.write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


def render_markdown(payload: dict[str, object]) -> str:
    blockers = payload["blockers"] or ["none"]
    self_test = payload["self_test"] or {}
    lines = [
        "# Confidentiality Support Audit",
        "",
        "Date: 2026-07-16",
        "",
        f"- AEAD supported locally: `{str(payload['aead_supported_locally']).lower()}`",
        f"- Implemented mechanism: {payload['implemented_mechanism']}",
        f"- Recommended mechanism: {payload['recommended_mechanism']}",
        f"- Claim status: `{payload['claim_status']}`",
        f"- Blockers: {'; '.join(blockers)}",
        "",
        "## Provider Status",
        "",
        f"- cryptography: `{str(payload['providers']['cryptography']).lower()}`",
        f"- pycryptodome: `{str(payload['providers']['pycryptodome']).lower()}`",
        "",
        "## AEAD Self-Test",
        "",
        f"- correct-key recovery: `{str(self_test.get('correct_key_recovers_plaintext', False)).lower()}`",
        f"- wrong-key authentication failure: `{str(self_test.get('wrong_key_authentication_fails', False)).lower()}`",
        f"- wrong-AAD authentication failure: `{str(self_test.get('wrong_associated_data_authentication_fails', False)).lower()}`",
        "",
        "## Policy",
        "",
        str(payload["policy"]),
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
