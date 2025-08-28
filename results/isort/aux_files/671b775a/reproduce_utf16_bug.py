#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from io import BytesIO
from isort.io import File

# Minimal reproduction of UTF-16 encoding detection bug
encoding_line = "# -*- coding: utf-16 -*-\n"
content = encoding_line
full_content = content.encode('utf-16')

buffer = BytesIO(full_content)
try:
    detected = File.detect_encoding("test.py", buffer.readline)
    print(f"Detected encoding: {detected}")
except Exception as e:
    print(f"Error: {e}")
    print(f"This is a bug - UTF-16 is a valid Python encoding and should be detected")