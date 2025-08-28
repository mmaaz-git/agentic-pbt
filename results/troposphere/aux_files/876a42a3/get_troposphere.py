#!/usr/bin/env python3

import os
import urllib.request
import json

# Get the latest version info
url = "https://pypi.org/simple/troposphere/"
try:
    with urllib.request.urlopen(url) as response:
        html = response.read().decode()
        # Extract the latest .tar.gz link
        import re
        matches = re.findall(r'href="([^"]+troposphere-[0-9.]+\.tar\.gz[^"]*)"', html)
        if matches:
            latest_url = matches[-1]  # Get the latest version
            if not latest_url.startswith('http'):
                latest_url = 'https://files.pythonhosted.org' + latest_url.split('../../files')[-1]
            print(f"Found troposphere URL: {latest_url}")
            
            # Download it
            import tempfile
            import tarfile
            with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as f:
                urllib.request.urlretrieve(latest_url, f.name)
                temp_path = f.name
            
            # Extract it
            with tarfile.open(temp_path, 'r:gz') as tar:
                tar.extractall('.')
            
            os.unlink(temp_path)
            print("Troposphere source downloaded and extracted")
        else:
            print("No troposphere package found")
except Exception as e:
    print(f"Error: {e}")