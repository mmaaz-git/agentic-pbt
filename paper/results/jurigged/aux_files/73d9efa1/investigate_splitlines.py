import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')

from jurigged.recode import splitlines
from ast import _splitlines_no_ff

# Test the failing case
text = '\n0'
print(f"Input: {repr(text)}")
print(f"jurigged.splitlines result: {splitlines(text)}")
print(f"ast._splitlines_no_ff result: {_splitlines_no_ff(text)}")

# Check codetools to see what splitlines implementation is actually used
import jurigged.codetools as codetools
print(f"\nCodetools splitlines: {codetools.splitlines}")
print(f"Python version: {sys.version}")

# Test more cases
test_cases = ['\n0', '0\n', '\n', 'a\nb', 'a\nb\n']
for case in test_cases:
    result = splitlines(case)
    print(f"\nInput: {repr(case)}")
    print(f"Result: {result}")
    print(f"Lines with endings: {[repr(line) for line in result]}")