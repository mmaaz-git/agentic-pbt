import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/djangorestframework-api-key_env/lib/python3.13/site-packages')

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'rest_framework_api_key',
        ],
        USE_TZ=True,
        SECRET_KEY='test-secret-key',
    )
    django.setup()

from rest_framework_api_key.crypto import concatenate, split

# Minimal failing example
left = "abc.def"
right = "xyz"

concatenated = concatenate(left, right)
result_left, result_right = split(concatenated)

print(f"Original left:  '{left}'")
print(f"Original right: '{right}'")
print(f"Concatenated:   '{concatenated}'")
print(f"Split left:     '{result_left}'")
print(f"Split right:    '{result_right}'")
print()

if result_left != left:
    print(f"❌ BUG: Left part mismatch!")
    print(f"   Expected: '{left}'")
    print(f"   Got:      '{result_left}'")
    
if result_right != right:
    print(f"❌ BUG: Right part mismatch!")
    print(f"   Expected: '{right}'")
    print(f"   Got:      '{result_right}'")

# Another edge case with just a dot
print("\nEdge case with dot as left:")
left2 = "."
right2 = "data"
concatenated2 = concatenate(left2, right2)
result_left2, result_right2 = split(concatenated2)

print(f"Original left:  '{left2}'")
print(f"Original right: '{right2}'")
print(f"Concatenated:   '{concatenated2}'")
print(f"Split left:     '{result_left2}'")
print(f"Split right:    '{result_right2}'")

if result_left2 != left2:
    print(f"❌ BUG: Left part mismatch!")
    print(f"   Expected: '{left2}'")
    print(f"   Got:      '{result_left2}'")