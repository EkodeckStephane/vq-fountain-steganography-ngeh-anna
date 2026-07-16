# Confidentiality Support Audit

Date: 2026-07-16

- AEAD supported locally: `true`
- Implemented mechanism: AES-256-GCM before ETHEGAN packetization
- Recommended mechanism: AES-GCM or XChaCha20-Poly1305 before ETHEGAN packetization
- Claim status: `supported`
- Blockers: none

## Provider Status

- cryptography: `true`
- pycryptodome: `true`

## AEAD Self-Test

- correct-key recovery: `true`
- wrong-key authentication failure: `true`
- wrong-AAD authentication failure: `true`

## Policy

Payload confidentiality may be claimed only for payloads encrypted before packetization with AEAD and rejected on authentication failure.
