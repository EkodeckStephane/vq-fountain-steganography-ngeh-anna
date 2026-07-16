from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from vq_fountain.bitstream import (
    PayloadDecodeError,
    bits_to_bytes,
    bytes_to_bits,
    pack_payload,
    unpack_payload,
)


class BitstreamTests(unittest.TestCase):
    def test_bits_roundtrip(self) -> None:
        data = b"abc\x00\xff"
        self.assertEqual(bits_to_bytes(bytes_to_bits(data)), data)

    def test_payload_roundtrip(self) -> None:
        payload = b"secret payload"
        self.assertEqual(unpack_payload(pack_payload(payload)), payload)

    def test_crc_rejects_corruption(self) -> None:
        packet = bytearray(pack_payload(b"secret payload"))
        packet[-1] ^= 0x01
        with self.assertRaises(PayloadDecodeError):
            unpack_payload(bytes(packet))


if __name__ == "__main__":
    unittest.main()
