import argparse
import json
import random
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from torch.utils.data import DataLoader, Dataset

from models import DenseDecoder512, DenseEncoder512, ResidualDenseEncoder512


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
TOTAL_BITS = 2 * 512 * 512


class ImageFolder512(Dataset):
    def __init__(self, roots, max_images=None, offset_images=0, max_images_per_root=None):
        self.paths = []
        for root in roots:
            root_paths = sorted(
                p for p in Path(root).rglob("*") if p.suffix.lower() in IMAGE_EXTENSIONS
            )
            if max_images_per_root:
                root_paths = root_paths[:max_images_per_root]
            self.paths.extend(root_paths)
        self.paths = sorted(self.paths)
        if offset_images:
            self.paths = self.paths[offset_images:]
        if max_images:
            self.paths = self.paths[:max_images]
        if not self.paths:
            raise ValueError(f"No images found under {root}")

    def __len__(self):
        return len(self.paths)

    def __getitem__(self, index):
        path = self.paths[index]
        image = Image.open(path).convert("RGB")
        width, height = image.size
        side = min(width, height)
        left = (width - side) // 2
        top = (height - side) // 2
        image = image.crop((left, top, left + side, top + side))
        image = image.resize((512, 512), Image.Resampling.BICUBIC)
        arr = np.asarray(image, dtype=np.float32) / 255.0
        tensor = torch.from_numpy(arr).permute(2, 0, 1)
        return (tensor - 0.5) / 0.5


def seed_everything(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def make_payload_and_mask(
    batch_size,
    bpp,
    device,
    padding_loss_weight,
    payload_mode,
    zero_tail_max_fraction,
):
    useful_bits = int(round(512 * 512 * bpp))
    if useful_bits < 1 or useful_bits > TOTAL_BITS:
        raise ValueError(f"bpp must imply 1..{TOTAL_BITS} bits; got {bpp}")
    flat = torch.zeros(batch_size, TOTAL_BITS, device=device)
    for row in range(batch_size):
        mode = payload_mode
        if payload_mode == "mixed":
            mode = "random" if random.random() < 0.5 else "zero_tail"
        if mode == "random":
            flat[row, :useful_bits] = torch.randint(0, 2, (useful_bits,), device=device).float()
        elif mode == "zero_tail":
            min_bits = min(useful_bits, 1024)
            max_bits = max(min_bits, int(useful_bits * zero_tail_max_fraction))
            active_bits = random.randint(min_bits, max_bits)
            flat[row, :active_bits] = torch.randint(0, 2, (active_bits,), device=device).float()
        else:
            raise ValueError(f"unknown payload_mode: {payload_mode}")
    mask = torch.full((batch_size, TOTAL_BITS), padding_loss_weight, device=device)
    mask[:, :useful_bits] = 1.0
    return flat.view(batch_size, 2, 512, 512), mask.view(batch_size, 2, 512, 512), useful_bits


def load_checkpoint_if_available(encoder, decoder, checkpoint_path, device):
    if not checkpoint_path:
        return
    checkpoint = torch.load(checkpoint_path, map_location=device)
    encoder.load_state_dict(checkpoint["en"], strict=True)
    decoder.load_state_dict(checkpoint["de"], strict=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-root", required=True, nargs="+")
    parser.add_argument("--output", required=True)
    parser.add_argument("--init-checkpoint")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--payload-bpp", type=float, default=0.25)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--lambda-extract", type=float, default=1.0)
    parser.add_argument("--lambda-image", type=float, default=10.0)
    parser.add_argument("--padding-loss-weight", type=float, default=0.02)
    parser.add_argument("--payload-mode", choices=["random", "zero_tail", "mixed"], default="random")
    parser.add_argument("--zero-tail-max-fraction", type=float, default=1.0)
    parser.add_argument("--encoder-mode", choices=["absolute", "residual"], default="residual")
    parser.add_argument("--residual-strength", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--max-images", type=int)
    parser.add_argument("--max-images-per-root", type=int)
    parser.add_argument("--offset-images", type=int, default=0)
    args = parser.parse_args()

    seed_everything(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    dataset = ImageFolder512(
        args.image_root, args.max_images, args.offset_images, args.max_images_per_root
    )
    loader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        drop_last=False,
    )

    if args.encoder_mode == "residual":
        encoder = ResidualDenseEncoder512(residual_strength=args.residual_strength).to(device)
    else:
        encoder = DenseEncoder512().to(device)
    decoder = DenseDecoder512().to(device)
    load_checkpoint_if_available(encoder, decoder, args.init_checkpoint, device)

    optimizer = torch.optim.Adam(
        list(encoder.parameters()) + list(decoder.parameters()),
        lr=args.lr,
        betas=(0.5, 0.999),
    )

    history = []
    for epoch in range(1, args.epochs + 1):
        encoder.train()
        decoder.train()
        epoch_loss = 0.0
        epoch_extract = 0.0
        epoch_image = 0.0
        epoch_ber = 0.0
        batches = 0

        for cover in loader:
            cover = cover.to(device)
            payload, loss_mask, useful_bits = make_payload_and_mask(
                cover.size(0),
                args.payload_bpp,
                device,
                args.padding_loss_weight,
                args.payload_mode,
                args.zero_tail_max_fraction,
            )

            stego = encoder(cover, payload)
            decoded = decoder(stego)

            per_bit_loss = F.binary_cross_entropy_with_logits(decoded, payload, reduction="none")
            extract_loss = (per_bit_loss * loss_mask).sum() / loss_mask.sum()
            image_loss = F.mse_loss(stego, cover)
            loss = args.lambda_extract * extract_loss + args.lambda_image * image_loss

            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()

            with torch.no_grad():
                pred = (decoded >= 0.0).float().reshape(cover.size(0), -1)
                target = payload.reshape(cover.size(0), -1)
                useful_bit_errors = (pred[:, :useful_bits] != target[:, :useful_bits]).float().mean()
                full_bit_errors = (pred != target).float().mean()

            epoch_loss += float(loss.item())
            epoch_extract += float(extract_loss.item())
            epoch_image += float(image_loss.item())
            epoch_ber += float(useful_bit_errors.item())
            batches += 1

        row = {
            "epoch": epoch,
            "loss": epoch_loss / batches,
            "extract_loss": epoch_extract / batches,
            "image_loss": epoch_image / batches,
            "useful_ber": epoch_ber / batches,
            "payload_bpp": args.payload_bpp,
            "payload_mode": args.payload_mode,
            "zero_tail_max_fraction": args.zero_tail_max_fraction,
        }
        history.append(row)
        print(json.dumps(row))

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "en": encoder.state_dict(),
            "de": decoder.state_dict(),
            "config": vars(args),
            "history": history,
        },
        output,
    )


if __name__ == "__main__":
    main()
