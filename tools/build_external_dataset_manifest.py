from __future__ import annotations

import argparse
import json
from pathlib import Path
import random


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".pgm", ".ppm", ".tif", ".tiff"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a sanitized manifest for external image datasets.")
    parser.add_argument("--dataset", action="append", nargs=2, metavar=("ALIAS", "ROOT"), required=True)
    parser.add_argument("--sample-size", type=int, default=1000)
    parser.add_argument("--seed", default="external-dataset-manifest")
    parser.add_argument("--out", default="05_artifacts/data/external_dataset_manifest.json")
    args = parser.parse_args()

    entries = []
    for alias, root_text in args.dataset:
        root = Path(root_text)
        files = sorted(path for path in root.rglob("*") if path.is_file())
        image_files = [path for path in files if path.suffix.lower() in IMAGE_EXTENSIONS]
        extension_counts: dict[str, int] = {}
        for path in files:
            extension = path.suffix.lower() or "<none>"
            extension_counts[extension] = extension_counts.get(extension, 0) + 1

        rng = random.Random(f"{args.seed}:{alias}")
        sample = image_files.copy()
        rng.shuffle(sample)
        sample = sample[: args.sample_size]
        entries.append(
            {
                "alias": alias,
                "total_files": len(files),
                "image_files": len(image_files),
                "extension_counts": dict(sorted(extension_counts.items())),
                "sample_size": len(sample),
                "sample_filenames": [path.name for path in sample[:20]],
            }
        )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"datasets": entries}, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"out": str(out_path), "datasets": entries}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
