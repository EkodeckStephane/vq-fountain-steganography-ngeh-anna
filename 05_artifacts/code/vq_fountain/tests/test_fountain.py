from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from vq_fountain.bitstream import pack_payload, unpack_payload
from vq_fountain.fountain import (
    FountainDecodeError,
    FountainSymbol,
    decode_symbols,
    encode_repetition_symbols,
    encode_symbols,
)
from vq_fountain.synthetic_channel import SyntheticChannelConfig, transmit_symbols


class FountainTests(unittest.TestCase):
    def test_decode_with_symbol_erasures(self) -> None:
        payload = b"VQ-Fountain payload " * 20
        packet = pack_payload(payload)
        symbols = encode_symbols(packet, block_size=24, overhead=1.2, seed="unit")
        delivered = transmit_symbols(
            symbols,
            SyntheticChannelConfig(symbol_erasure_rate=0.20, bit_flip_rate=0.0, seed="unit"),
        )
        recovered = unpack_payload(decode_symbols(delivered))
        self.assertEqual(recovered, payload)

    def test_systematic_roundtrip_without_loss(self) -> None:
        payload = b"short"
        packet = pack_payload(payload)
        symbols = encode_symbols(packet, block_size=8, overhead=0.0, seed=7)
        recovered = unpack_payload(decode_symbols(symbols))
        self.assertEqual(recovered, payload)

    def test_repetition_baseline_roundtrip_without_loss(self) -> None:
        payload = b"fixed repetition baseline"
        packet = pack_payload(payload)
        symbols = encode_repetition_symbols(packet, block_size=8, overhead=1.0)
        recovered = unpack_payload(decode_symbols(symbols))
        self.assertEqual(recovered, payload)

    def test_symbol_crc_turns_corruption_into_erasure(self) -> None:
        payload = b"crc guarded payload " * 8
        packet = pack_payload(payload)
        symbols = encode_symbols(packet, block_size=8, overhead=1.5, seed="crc")
        corrupted = []
        for index, symbol in enumerate(symbols):
            if index % 5 == 0:
                data = bytearray(symbol.data)
                data[0] ^= 0x01
                corrupted.append(
                    FountainSymbol(
                        symbol_id=symbol.symbol_id,
                        source_count=symbol.source_count,
                        block_size=symbol.block_size,
                        original_size=symbol.original_size,
                        block_ids=symbol.block_ids,
                        data=bytes(data),
                        data_crc=symbol.data_crc,
                    )
                )
            else:
                corrupted.append(symbol)

        recovered = unpack_payload(decode_symbols(corrupted))
        self.assertEqual(recovered, payload)

    def test_all_corrupted_crc_symbols_are_rejected(self) -> None:
        symbols = encode_symbols(b"abcdefgh", block_size=4, overhead=0.0, seed="bad")
        corrupted = []
        for symbol in symbols:
            data = bytearray(symbol.data)
            data[0] ^= 0x01
            corrupted.append(
                FountainSymbol(
                    symbol_id=symbol.symbol_id,
                    source_count=symbol.source_count,
                    block_size=symbol.block_size,
                    original_size=symbol.original_size,
                    block_ids=symbol.block_ids,
                    data=bytes(data),
                    data_crc=symbol.data_crc,
                )
            )
        with self.assertRaises(FountainDecodeError):
            decode_symbols(corrupted)


if __name__ == "__main__":
    unittest.main()
