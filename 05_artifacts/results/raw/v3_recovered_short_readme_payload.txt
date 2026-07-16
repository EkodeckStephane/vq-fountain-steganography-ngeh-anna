## Requirements

```bash
pip install torch torchvision numpy pillow reedsolo
```
FILES NEEDED
~/ETEHGAN
│
├── ETEHGAN.pt                  # Trained deep learning model weights
├── image dataset                # Sample baseline cover image
├── large_story.txt             # Sample massive secret text payload
│
├── embed_payload.py            # Neural Embedding Script (Sender Layer)
├── extract_payload.py          # Neural Extraction Script (Receiver Layer)

STEPS
A. sender
1. python embed_payload.py <cover_image_path.jpg> <secret_text_path.txt> <output_stego.png> <ETEHGAN.pt>
2. send to the receiver
 B. Receiver
 1. Go to the dataset online and download the cover image
 2. python extract_payload.py <stego_image_path.jpg> <output_recovered_text_path.txt> <ETEHGAN.pt>

metric


🏆 SCALE-RESTORED GENERALIZATION METRICS
=============================================
📈 Configuration Target : 2.0 bpp (512x512)
📊 Total Bitstream Size : 524,288 bits
---------------------------------------------
🖼️ Generalization SSIM : 0.8498
🔊 Generalization PSNR : 30.05 dB
🛑 Hold-Out BER        : 0.2513%