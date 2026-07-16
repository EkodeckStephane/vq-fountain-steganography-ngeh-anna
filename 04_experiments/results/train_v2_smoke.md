# V2 Training Smoke Run

Date: 2026-07-13

Command:

```powershell
python 05_artifacts\code\etehgan\train_v2.py --image-root 05_artifacts\data\sample_images --output 05_artifacts\models\etehgan_v2_smoke.pt --init-checkpoint 05_artifacts\models\ETEHGAN.pt --epochs 1 --payload-bpp 0.25 --lambda-image 10 --batch-size 1
```

Result:

```json
{"epoch": 1, "loss": 4.027984857559204, "extract_loss": 2.492966413497925, "image_loss": 0.15350183099508286, "ber": 0.44539928436279297}
```

Interpretation:

The script executes and writes a checkpoint. This run is not a scientific result because it uses only the two sample images and one epoch. It only validates that the V2 training path is runnable.

