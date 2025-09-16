import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/storage3_env/lib/python3.13/site-packages')

from storage3.types import UploadResponse
from dataclasses import asdict

# Create instance using the custom __init__
response = UploadResponse(path='test/file.txt', Key='bucket/test/file.txt')

# Try to use asdict - this will fail because UploadResponse isn't properly a dataclass
try:
    asdict(response)
    print("asdict worked - no bug")
except TypeError as e:
    print(f"BUG FOUND: asdict fails with: {e}")
    print("Reason: UploadResponse has @dataclass decorator but custom __init__ breaks dataclass functionality")