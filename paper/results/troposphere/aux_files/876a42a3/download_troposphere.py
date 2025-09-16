#!/usr/bin/env python3

import os
import urllib.request
import tarfile
import tempfile

# Download troposphere source
url = "https://files.pythonhosted.org/packages/source/t/troposphere/troposphere-4.8.4.tar.gz"
with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as f:
    urllib.request.urlretrieve(url, f.name)
    temp_path = f.name

# Extract it
with tarfile.open(temp_path, 'r:gz') as tar:
    tar.extractall('.')

os.unlink(temp_path)
print("Troposphere source downloaded and extracted")