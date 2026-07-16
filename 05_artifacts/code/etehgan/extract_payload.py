# extract_payload.py
import sys
import torch
import numpy as np
from PIL import Image
from reedsolo import RSCodec, ReedSolomonError
from models import DenseDecoder512

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
ecc_engine = RSCodec(32)

def pil_to_normalized_tensor(pil_image):
    arr = np.asarray(pil_image.convert('RGB'), dtype=np.float32) / 255.0
    tensor = torch.from_numpy(arr).permute(2, 0, 1)
    return (tensor - 0.5) / 0.5

def bits_to_text(bit_tensor):
    bits = (bit_tensor >= 0.0).int().cpu().numpy().flatten()
    
    # Log total bits extracted out of the neural network layers
    print(f"[extract] Bits extracted from model structure: {len(bits)} bits")
    
    extracted_bytes = []
    for i in range(0, len(bits), 8):
        byte_bits = bits[i:i+8]
        if len(byte_bits) < 8: break
        extracted_bytes.append(int("".join(str(b) for b in byte_bits), 2))
        
    payload_bytes = bytearray()
    for j in range(len(extracted_bytes) - 1):
        if extracted_bytes[j] == 0 and extracted_bytes[j+1] == 0: # Null delimiter match
            break
        payload_bytes.append(extracted_bytes[j])
        
    try:
        decoded_output = ecc_engine.decode(payload_bytes)
        
        if isinstance(decoded_output, (tuple, list)):
            corrected_bytes = decoded_output[0]
        else:
            corrected_bytes = decoded_output
            
        return bytearray(corrected_bytes).decode('utf-8')
        
    except (ReedSolomonError, UnicodeDecodeError):
        return "❌ Transmission Recovery Failed: Uncorrectable structural damage."

def extract(stego_path, output_file_path, weights_path):
    print("[extract] Running step 2: processing received asset...")
    decoder = DenseDecoder512().to(device).eval()
    
    checkpoint = torch.load(weights_path, map_location=device)
    decoder.load_state_dict(checkpoint['de'])
    
    image = Image.open(stego_path).convert('RGB').resize((512, 512), Image.Resampling.BICUBIC)
    stego_tensor = pil_to_normalized_tensor(image).unsqueeze(0).to(device)
    
    with torch.no_grad():
        decoded_output = decoder(stego_tensor)
        recovered_text = bits_to_text(decoded_output)
        
    with open(output_file_path, 'w', encoding='utf-8', newline='') as f:
        f.write(recovered_text)
        
    print(f"[extract] Secret payload recovered and saved to: '{output_file_path}'")

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python extract_payload.py <stego_image_png> <output_txt_file> <weights_pt>")
    else:
        extract(sys.argv[1], sys.argv[2], sys.argv[3])
