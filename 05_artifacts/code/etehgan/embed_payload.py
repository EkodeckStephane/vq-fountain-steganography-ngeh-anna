# embed_payload.py
import sys
import os
import torch
import numpy as np
from PIL import Image, ImageFilter
from reedsolo import RSCodec, ReedSolomonError
from models import DenseEncoder512, DenseDecoder512

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
ecc_engine = RSCodec(32)

def pil_to_normalized_tensor(pil_image):
    arr = np.asarray(pil_image.convert('RGB'), dtype=np.float32) / 255.0
    tensor = torch.from_numpy(arr).permute(2, 0, 1)
    return (tensor - 0.5) / 0.5

def text_to_bits(text, total_bits=524288):
    raw_bytes = text.encode('utf-8')
    ecc_bytes = ecc_engine.encode(raw_bytes)
    bits = []
    for b in ecc_bytes:
        bits.extend([int(x) for x in f"{b:08b}"])
    bits.extend([0] * 16) # Null delimiter flag
    
    print(f"[payload] Bits to be embedded (payload + ECC + delimiter): {len(bits)} bits")
    
    if len(bits) > total_bits:
        raise ValueError(f"💥 Payload too large! Needed {len(bits)} bits, Max is {total_bits}.")
        
    if len(bits) < total_bits:
        # Pad with random bits to completely fill the 524,288 bit capacity
        bits.extend(np.random.randint(0, 2, total_bits - len(bits)).tolist())
        
    return torch.tensor(bits).float().view(2, 512, 512).unsqueeze(0).to(device)

def process_cover_image(image_path):
    """Checks image constraints, applies center-cropping and sharpening if required."""
    img = Image.open(image_path).convert('RGB')
    width, height = img.size
    
    if width == 512 and height == 512:
        print("[image] Cover image is already optimal (512x512). Skipping transformation layers.")
        return img
    
    print(f"[image] Dimensions detected: {width}x{height}. Activating quality-preserved scaling...")
    
    min_side = min(width, height)
    left = (width - min_side) / 2
    top = (height - min_side) / 2
    right = (width + min_side) / 2
    bottom = (height + min_side) / 2
    img_square = img.crop((left, top, right, bottom))
    
    img_resized = img_square.resize((512, 512), Image.Resampling.BICUBIC)
    img_sharper = img_resized.filter(ImageFilter.UnsharpMask(radius=1, percent=100, threshold=3))
    return img_sharper

def analyze_image_entropy(pil_image):
    """Calculates image spatial variance to predict extraction compatibility."""
    img_gray = pil_image.convert('L')
    arr = np.array(img_gray)
    variance = np.var(arr)
    
    print(f"[image] Texture diagnostic: structural variance = {variance:.2f}")
    if variance < 800.0:
        print("[warning] This cover image has large flat surfaces (low entropy).")
        print("    High-density embedding might suffer from localized channel noise.")
    else:
        print("[image] Image structure contains strong texture depth for high-capacity steganography.")

def verify_stego_channel_integrity(stego_img_obj, weights_path):
    """Simulates the receiver's extraction locally to guarantee transmission success."""
    print("[verify] Initiating loopback verification test...")
    decoder = DenseDecoder512().to(device).eval()
    
    checkpoint = torch.load(weights_path, map_location=device)
    decoder.load_state_dict(checkpoint['de'])
    
    stego_tensor = pil_to_normalized_tensor(stego_img_obj).unsqueeze(0).to(device)
    
    with torch.no_grad():
        decoded_output = decoder(stego_tensor)
        bits = (decoded_output >= 0.0).int().cpu().numpy().flatten()
        
    extracted_bytes = []
    for i in range(0, len(bits), 8):
        byte_bits = bits[i:i+8]
        if len(byte_bits) < 8: break
        extracted_bytes.append(int("".join(str(b) for b in byte_bits), 2))
        
    payload_bytes = bytearray()
    for j in range(len(extracted_bytes) - 1):
        if extracted_bytes[j] == 0 and extracted_bytes[j+1] == 0:
            break
        payload_bytes.append(extracted_bytes[j])
        
    try:
        # Check if the local Reed-Solomon engine can clean up the errors
        ecc_engine.decode(payload_bytes)
        print("[verify] Transmission assured: loopback test passed.")
    except (ReedSolomonError, UnicodeDecodeError):
        print("[warning] Transmission failure risk: this stego image generated uncorrectable bit errors.")
        print("   -> Reason: Rounding noise completely wiped the fragile neural patterns on these surfaces.")
        print("   -> Action Needed: Please drop this file and choose an image with richer textures.")

def embed(cover_path, message_file_path, output_stego_path, weights_path):
    print("[embed] Running step 1: initializing stego generation asset...")
    encoder = DenseEncoder512().to(device).eval()
    
    checkpoint = torch.load(weights_path, map_location=device)
    encoder.load_state_dict(checkpoint['en'])
    
    with open(message_file_path, 'r', encoding='utf-8', newline='') as f:
        secret_text = f.read()
        
    clean_cover_img = process_cover_image(cover_path)
    analyze_image_entropy(clean_cover_img)
    
    cover_tensor = pil_to_normalized_tensor(clean_cover_img).unsqueeze(0).to(device)
    message_tensor = text_to_bits(secret_text)
    
    with torch.no_grad():
        stego_tensor = encoder(cover_tensor, message_tensor)
        stego_clamped = ((stego_tensor.squeeze(0) + 1.0) * 127.5).clamp(0, 255).cpu().byte().permute(1, 2, 0).numpy()
        stego_final_image = Image.fromarray(stego_clamped)
        
        # Execute the receiver side check right before committing to disk
        verify_stego_channel_integrity(stego_final_image, weights_path)
        
        stego_final_image.save(output_stego_path)
        
    print(f"[embed] Production stego image successfully generated: '{output_stego_path}'\n")

if __name__ == '__main__':
    if len(sys.argv) < 5:
        print("Usage: python embed_payload.py <cover_image> <secret_txt_file> <output_stego_png> <weights_pt>")
    else:
        embed(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
