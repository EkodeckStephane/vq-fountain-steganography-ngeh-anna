import argparse
import json
import random
from pathlib import Path

import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader

from models import DenseDecoder512, DenseEncoder512, ResidualDenseEncoder512
from steg_losses import residual_statistics_loss
from train_v2 import ImageFolder512, make_payload_and_mask, seed_everything


def build_encoder(args):
    if args.encoder_mode == "residual":
        return ResidualDenseEncoder512(residual_strength=args.residual_strength)
    return DenseEncoder512()


def load_checkpoint(encoder, decoder, checkpoint_path, device):
    checkpoint = torch.load(checkpoint_path, map_location=device)
    encoder.load_state_dict(checkpoint["en"], strict=True)
    decoder.load_state_dict(checkpoint["de"], strict=True)
    return checkpoint


def quantize_ste(x, levels):
    quantized = torch.round(x * levels) / levels
    return x + (quantized - x).detach()


def avg_blur(x, kernel_size):
    channels = x.shape[1]
    weight = x.new_ones(channels, 1, kernel_size, kernel_size) / float(kernel_size * kernel_size)
    return F.conv2d(x, weight, padding=kernel_size // 2, groups=channels)


def jpeg_surrogate(x, quality):
    # Differentiable proxy for JPEG-like quantization and mild low-pass loss.
    # It is not a JPEG implementation; actual JPEG remains evaluated separately.
    y = (x + 1.0) * 0.5
    if quality <= 80:
        low = avg_blur(y, 5)
        blend = 0.35
        levels = 32.0
    elif quality <= 90:
        low = avg_blur(y, 3)
        blend = 0.25
        levels = 48.0
    else:
        low = avg_blur(y, 3)
        blend = 0.15
        levels = 64.0
    y = (1.0 - blend) * y + blend * low
    y = quantize_ste(y.clamp(0.0, 1.0), levels)
    return (2.0 * y - 1.0).clamp(-1.0, 1.0)


def apply_attack(x, attack, args):
    if attack == "clean":
        return x
    if attack == "noise":
        return (x + torch.randn_like(x) * args.noise_sigma).clamp(-1.0, 1.0)
    if attack == "blur":
        return avg_blur(x, args.blur_kernel).clamp(-1.0, 1.0)
    if attack == "resize":
        small = F.interpolate(x, scale_factor=args.resize_scale, mode="bilinear", align_corners=False)
        return F.interpolate(small, size=x.shape[-2:], mode="bilinear", align_corners=False).clamp(-1.0, 1.0)
    if attack == "jpeg95":
        return jpeg_surrogate(x, 95)
    if attack == "jpeg90":
        return jpeg_surrogate(x, 90)
    if attack == "jpeg80":
        return jpeg_surrogate(x, 80)
    raise ValueError(f"unknown attack: {attack}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-root", required=True, nargs="+")
    parser.add_argument("--output", required=True)
    parser.add_argument("--init-checkpoint")
    parser.add_argument("--resume-checkpoint")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--payload-bpp", type=float, default=0.05)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--lambda-clean", type=float, default=0.5)
    parser.add_argument("--lambda-attack", type=float, default=1.0)
    parser.add_argument("--lambda-image", type=float, default=20.0)
    parser.add_argument("--lambda-stat", type=float, default=0.25)
    parser.add_argument("--padding-loss-weight", type=float, default=0.02)
    parser.add_argument("--payload-mode", choices=["random", "zero_tail", "mixed"], default="random")
    parser.add_argument("--zero-tail-max-fraction", type=float, default=1.0)
    parser.add_argument("--encoder-mode", choices=["absolute", "residual"], default="residual")
    parser.add_argument("--residual-strength", type=float, default=0.18)
    parser.add_argument("--attacks", nargs="+", default=["clean", "jpeg95", "blur", "resize"])
    parser.add_argument("--noise-sigma", type=float, default=0.01)
    parser.add_argument("--blur-kernel", type=int, default=3)
    parser.add_argument("--resize-scale", type=float, default=0.75)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--max-images", type=int)
    parser.add_argument("--max-images-per-root", type=int)
    parser.add_argument("--offset-images", type=int, default=0)
    args = parser.parse_args()

    seed_everything(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    dataset = ImageFolder512(
        args.image_root,
        max_images=args.max_images,
        offset_images=args.offset_images,
        max_images_per_root=args.max_images_per_root,
    )
    loader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        drop_last=False,
    )

    encoder = build_encoder(args).to(device)
    decoder = DenseDecoder512().to(device)
    if args.resume_checkpoint:
        checkpoint = load_checkpoint(encoder, decoder, args.resume_checkpoint, device)
        history = list(checkpoint.get("history", []))
    elif args.init_checkpoint:
        load_checkpoint(encoder, decoder, args.init_checkpoint, device)
        history = []
    else:
        raise SystemExit("Provide --init-checkpoint for a fresh run or --resume-checkpoint to continue.")

    optimizer = torch.optim.Adam(
        list(encoder.parameters()) + list(decoder.parameters()),
        lr=args.lr,
        betas=(0.5, 0.999),
    )

    completed_epochs = [
        int(row.get("epoch", index + 1))
        for index, row in enumerate(history)
        if isinstance(row, dict)
    ]
    start_epoch = (max(completed_epochs) if completed_epochs else 0) + 1
    if start_epoch > args.epochs:
        print(
            json.dumps(
                {
                    "status": "already_complete",
                    "completed_epochs": completed_epochs,
                    "target_epochs": args.epochs,
                }
            ),
            flush=True,
        )

    for epoch in range(start_epoch, args.epochs + 1):
        encoder.train()
        decoder.train()
        totals = {
            "loss": 0.0,
            "clean_extract_loss": 0.0,
            "attack_extract_loss": 0.0,
            "image_loss": 0.0,
            "stat_loss": 0.0,
            "clean_ber": 0.0,
            "attack_ber": 0.0,
        }
        attack_counts = {attack: 0 for attack in args.attacks}
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
            attack = random.choice(args.attacks)
            attacked = apply_attack(stego, attack, args)
            attack_counts[attack] += 1

            clean_logits = decoder(stego)
            attack_logits = decoder(attacked)
            clean_loss = F.binary_cross_entropy_with_logits(clean_logits, payload, reduction="none")
            attack_loss = F.binary_cross_entropy_with_logits(attack_logits, payload, reduction="none")
            clean_extract_loss = (clean_loss * loss_mask).sum() / loss_mask.sum()
            attack_extract_loss = (attack_loss * loss_mask).sum() / loss_mask.sum()
            image_loss = F.mse_loss(stego, cover)
            stat_loss = residual_statistics_loss(cover, stego)

            loss = (
                args.lambda_clean * clean_extract_loss
                + args.lambda_attack * attack_extract_loss
                + args.lambda_image * image_loss
                + args.lambda_stat * stat_loss
            )

            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()

            with torch.no_grad():
                target = payload.reshape(cover.size(0), -1)
                clean_pred = (clean_logits >= 0.0).float().reshape(cover.size(0), -1)
                attack_pred = (attack_logits >= 0.0).float().reshape(cover.size(0), -1)
                clean_ber = (clean_pred[:, :useful_bits] != target[:, :useful_bits]).float().mean()
                attack_ber = (attack_pred[:, :useful_bits] != target[:, :useful_bits]).float().mean()

            totals["loss"] += float(loss.item())
            totals["clean_extract_loss"] += float(clean_extract_loss.item())
            totals["attack_extract_loss"] += float(attack_extract_loss.item())
            totals["image_loss"] += float(image_loss.item())
            totals["stat_loss"] += float(stat_loss.item())
            totals["clean_ber"] += float(clean_ber.item())
            totals["attack_ber"] += float(attack_ber.item())
            batches += 1

        row = {key: value / batches for key, value in totals.items()}
        row.update(
            {
                "epoch": epoch,
                "payload_bpp": args.payload_bpp,
                "lambda_clean": args.lambda_clean,
                "lambda_attack": args.lambda_attack,
                "lambda_image": args.lambda_image,
                "lambda_stat": args.lambda_stat,
                "attack_counts": attack_counts,
            }
        )
        history.append(row)
        print(json.dumps(row), flush=True)

        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        epoch_output = output.with_name(f"{output.stem}_epoch{epoch}{output.suffix}")
        torch.save(
            {
                "en": encoder.state_dict(),
                "de": decoder.state_dict(),
                "config": vars(args),
                "history": history,
            },
            epoch_output,
        )

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
