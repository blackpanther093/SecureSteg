#!/usr/bin/env python3
"""Comprehensive test of all SecureSteg features."""

import requests
import numpy as np
import cv2
import tempfile
import time

print("\n" + "=" * 70)
print(" " * 15 + "COMPREHENSIVE FEATURE TEST")
print("=" * 70)

# Create test image
img = np.random.randint(20, 240, (400, 400, 3), dtype=np.uint8)
tmp_img = tempfile.mktemp(suffix='.png')
cv2.imwrite(tmp_img, img)

tests = [
    ("Basic LSB", {"method": "lsb", "encryption_mode": "auto"}),
    ("Multi-Layer LSB", {"method":"multi_layer_lsb", "encryption_mode": "auto"}),
    ("Spread Spectrum", {"method": "spread_spectrum", "encryption_mode": "auto"}),
    ("Histogram Shift", {"method": "histogram_shifting", "encryption_mode": "auto"}),
    ("24hr Expiration", {"self_destruct_mode": "24_hours", "encryption_mode": "auto"}),
    ("One-Decode Destruct", {"self_destruct_mode": "one_decode", "encryption_mode": "auto"}),
    ("Hidden Watermark", {"watermark_mode": "hidden", "encryption_mode": "auto"}),
    ("Manual Password", {"encryption_mode": "manual", "password": "test123"}),
]

success_count = 0
for name, options in tests:
    try:
        with open(tmp_img, 'rb') as f:
            data = {
                'secret_message': f'Test Message: {name}',
                'method': options.get('method', 'multi_layer_lsb'),
                'encryption_mode': options.get('encryption_mode', 'auto'),
                'self_destruct_mode': options.get('self_destruct_mode', 'unlimited'),
                'watermark_mode': options.get('watermark_mode', 'hidden'),
                'password': options.get('password', ''),
                'compression': 'true'
            }
            
            r = requests.post(
                'http://localhost:8000/embed',
                files={'file': ('test.png', f)},
                data=data,
                timeout=15
            )
        
        if r.status_code == 200:
            resp = r.json()
            key_display = str(resp.get('recovery_key', 'N/A'))[:25]
            if len(str(resp.get('recovery_key'))) > 25:
                key_display += "..."
            print(f"✓ {name:25} | Key: {key_display}")
            success_count += 1
        else:
            print(f"✗ {name:25} | HTTP {r.status_code}")
            
    except Exception as e:
        print(f"✗ {name:25} | Error: {str(e)[:40]}")
    
    time.sleep(0.3)

print("=" * 70)
print(f"Results: {success_count}/{len(tests)} tests passed")
print("=" * 70 + "\n")
