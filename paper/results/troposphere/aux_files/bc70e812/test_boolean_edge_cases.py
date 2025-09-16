import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import boolean

test_values = [
    "1",      # string "1" 
    1,        # integer 1
    "0",      # string "0"
    0,        # integer 0
    "TRUE",   # uppercase variation
    "FALSE",  # uppercase variation
    " true ", # with spaces
    "",       # empty string
    2,        # integer other than 0/1
    -1,       # negative integer
]

for value in test_values:
    try:
        result = boolean(value)
        print(f"boolean({repr(value)}) = {result}")
    except (ValueError, TypeError) as e:
        print(f"boolean({repr(value)}) raised: {e}")