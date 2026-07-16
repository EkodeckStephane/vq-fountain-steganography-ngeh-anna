from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from vq_fountain.bitstream import PayloadDecodeError, pack_payload, unpack_payload
from vq_fountain.fountain import FountainDecodeError, decode_symbols, encode_symbols
from vq_fountain.synthetic_channel import SyntheticChannelConfig, transmit_symbols


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a synthetic VQ-Fountain recovery smoke test.")
    parser.add_argument("--message", default="VQ-Fountain smoke test")
    parser.add_argument("--block-size", type=int, default=24)
    parser.add_argument("--overhead", type=float, default=0.8)
    parser.add_argument("--erasure-rate", type=float, default=0.2)
    parser.add_argument("--bit-flip-rate", type=float, default=0.0)
    parser.add_argument("--seed", default="smoke")
    args = parser.parse_args()

    payload = args.message.encode("utf-8")
    packet = pack_payload(payload)
    symbols = encode_symbols(packet, block_size=args.block_size, overhead=args.overhead, seed=args.seed)
    delivered = transmit_symbols(
        symbols,
        SyntheticChannelConfig(
            symbol_erasure_rate=args.erasure_rate,
            bit_flip_rate=args.bit_flip_rate,
            seed=args.seed,
        ),
    )

    result: dict[str, object] = {
        "payload_bytes": len(payload),
        "packet_bytes": len(packet),
        "source_symbols": symbols[0].source_count if symbols else 0,
        "encoded_symbols": len(symbols),
        "delivered_symbols": len(delivered),
        "erasure_rate": args.erasure_rate,
        "bit_flip_rate": args.bit_flip_rate,
        "exact_recovery": False,
    }

    try:
        recovered_packet = decode_symbols(delivered)
        recovered_payload = unpack_payload(recovered_packet)
        result["exact_recovery"] = recovered_payload == payload
        result["decoded_message"] = recovered_payload.decode("utf-8", errors="replace")
    except (FountainDecodeError, PayloadDecodeError) as exc:
        result["failure"] = str(exc)

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["exact_recovery"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
