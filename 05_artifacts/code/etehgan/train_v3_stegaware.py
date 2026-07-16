import argparse
import json
from pathlib import Path

import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader

from models import (
    DenseDecoder512,
    DenseEncoder512,
    ResidualDenseEncoder512,
    ResidualStegoDiscriminator,
)
from steg_losses import residual_statistics_loss
from train_v2 import ImageFolder512, make_payload_and_mask, seed_everything


def build_encoder(args):
    if args.encoder_mode == "residual":
        return ResidualDenseEncoder512(residual_strength=args.residual_strength)
    return DenseEncoder512()


def load_checkpoint(encoder, decoder, discriminator, checkpoint_path, device, load_discriminator=False):
    if not checkpoint_path:
        return
    checkpoint = torch.load(checkpoint_path, map_location=device)
    encoder.load_state_dict(checkpoint["en"], strict=True)
    decoder.load_state_dict(checkpoint["de"], strict=True)
    if load_discriminator and discriminator is not None and "sd" in checkpoint:
        discriminator.load_state_dict(checkpoint["sd"], strict=True)


def set_requires_grad(module, value):
    for parameter in module.parameters():
        parameter.requires_grad_(value)


def discriminator_loss(discriminator, cover, stego):
    real_logits = discriminator(cover)
    fake_logits = discriminator(stego.detach())
    real_targets = torch.zeros_like(real_logits)
    fake_targets = torch.ones_like(fake_logits)
    real_loss = F.binary_cross_entropy_with_logits(real_logits, real_targets)
    fake_loss = F.binary_cross_entropy_with_logits(fake_logits, fake_targets)
    loss = 0.5 * (real_loss + fake_loss)
    with torch.no_grad():
        real_ok = (real_logits < 0).float().mean()
        fake_ok = (fake_logits >= 0).float().mean()
        accuracy = 0.5 * (real_ok + fake_ok)
    return loss, accuracy


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-root", required=True, nargs="+")
    parser.add_argument("--output", required=True)
    parser.add_argument("--init-checkpoint")
    parser.add_argument("--load-discriminator", action="store_true")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--payload-bpp", type=float, default=0.25)
    parser.add_argument("--lr", type=float, default=5e-5)
    parser.add_argument("--disc-lr", type=float, default=1e-4)
    parser.add_argument("--lambda-extract", type=float, default=1.0)
    parser.add_argument("--lambda-image", type=float, default=16.0)
    parser.add_argument("--lambda-stat", type=float, default=0.5)
    parser.add_argument("--lambda-adv", type=float, default=0.01)
    parser.add_argument("--disc-steps", type=int, default=1)
    parser.add_argument("--disc-base-channels", type=int, default=16)
    parser.add_argument("--padding-loss-weight", type=float, default=0.02)
    parser.add_argument("--payload-mode", choices=["random", "zero_tail", "mixed"], default="random")
    parser.add_argument("--zero-tail-max-fraction", type=float, default=1.0)
    parser.add_argument("--encoder-mode", choices=["absolute", "residual"], default="residual")
    parser.add_argument("--residual-strength", type=float, default=0.18)
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
    discriminator = ResidualStegoDiscriminator(args.disc_base_channels).to(device)
    load_checkpoint(
        encoder,
        decoder,
        discriminator,
        args.init_checkpoint,
        device,
        load_discriminator=args.load_discriminator,
    )

    optimizer = torch.optim.Adam(
        list(encoder.parameters()) + list(decoder.parameters()),
        lr=args.lr,
        betas=(0.5, 0.999),
    )
    disc_optimizer = torch.optim.Adam(
        discriminator.parameters(),
        lr=args.disc_lr,
        betas=(0.5, 0.999),
    )

    history = []
    for epoch in range(1, args.epochs + 1):
        encoder.train()
        decoder.train()
        discriminator.train()
        totals = {
            "loss": 0.0,
            "extract_loss": 0.0,
            "image_loss": 0.0,
            "stat_loss": 0.0,
            "adv_loss": 0.0,
            "disc_loss": 0.0,
            "disc_accuracy": 0.0,
            "useful_ber": 0.0,
        }
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

            disc_loss_value = cover.new_tensor(0.0)
            disc_accuracy_value = cover.new_tensor(0.0)
            if args.lambda_adv > 0 and args.disc_steps > 0:
                set_requires_grad(discriminator, True)
                for _ in range(args.disc_steps):
                    with torch.no_grad():
                        stego_for_disc = encoder(cover, payload)
                    disc_loss_value, disc_accuracy_value = discriminator_loss(
                        discriminator,
                        cover,
                        stego_for_disc,
                    )
                    disc_optimizer.zero_grad(set_to_none=True)
                    disc_loss_value.backward()
                    disc_optimizer.step()

            set_requires_grad(discriminator, False)
            stego = encoder(cover, payload)
            decoded = decoder(stego)

            per_bit_loss = F.binary_cross_entropy_with_logits(decoded, payload, reduction="none")
            extract_loss = (per_bit_loss * loss_mask).sum() / loss_mask.sum()
            image_loss = F.mse_loss(stego, cover)
            stat_loss = residual_statistics_loss(cover, stego)
            if args.lambda_adv > 0:
                adv_logits = discriminator(stego)
                adv_loss = F.binary_cross_entropy_with_logits(
                    adv_logits,
                    torch.zeros_like(adv_logits),
                )
            else:
                adv_loss = cover.new_tensor(0.0)

            loss = (
                args.lambda_extract * extract_loss
                + args.lambda_image * image_loss
                + args.lambda_stat * stat_loss
                + args.lambda_adv * adv_loss
            )

            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
            set_requires_grad(discriminator, True)

            with torch.no_grad():
                pred = (decoded >= 0.0).float().reshape(cover.size(0), -1)
                target = payload.reshape(cover.size(0), -1)
                useful_bit_errors = (pred[:, :useful_bits] != target[:, :useful_bits]).float().mean()

            totals["loss"] += float(loss.item())
            totals["extract_loss"] += float(extract_loss.item())
            totals["image_loss"] += float(image_loss.item())
            totals["stat_loss"] += float(stat_loss.item())
            totals["adv_loss"] += float(adv_loss.item())
            totals["disc_loss"] += float(disc_loss_value.item())
            totals["disc_accuracy"] += float(disc_accuracy_value.item())
            totals["useful_ber"] += float(useful_bit_errors.item())
            batches += 1

        row = {key: value / batches for key, value in totals.items()}
        row.update(
            {
                "epoch": epoch,
                "payload_bpp": args.payload_bpp,
                "payload_mode": args.payload_mode,
                "lambda_image": args.lambda_image,
                "lambda_stat": args.lambda_stat,
                "lambda_adv": args.lambda_adv,
                "disc_steps": args.disc_steps,
            }
        )
        history.append(row)
        print(json.dumps(row))

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "en": encoder.state_dict(),
            "de": decoder.state_dict(),
            "sd": discriminator.state_dict(),
            "config": vars(args),
            "history": history,
        },
        output,
    )


if __name__ == "__main__":
    main()
