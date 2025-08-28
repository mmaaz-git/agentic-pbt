import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pdfkit_env/lib/python3.13/site-packages')

from pdfkit.pdfkit import PDFKit
from pdfkit.configuration import Configuration

# Mock configuration to bypass wkhtmltopdf check
class MockConfig:
    def __init__(self):
        self.wkhtmltopdf = '/usr/bin/wkhtmltopdf'  # Fake path
        self.meta_tag_prefix = 'pdfkit-'
        self.environ = {}

# Test: What happens when a user passes a non-string to from_string?
# This is a realistic scenario - users might pass numbers, None, etc.
print("Testing PDFKit with non-string inputs...")

test_inputs = [
    42,           # Common: numeric content
    3.14,         # Float 
    None,         # Null value
    True,         # Boolean
]

for input_val in test_inputs:
    print(f"\nInput: {input_val} (type: {type(input_val).__name__})")
    try:
        pdf = PDFKit(input_val, 'string', configuration=MockConfig())
        # Try to generate command which will call to_s()
        cmd = pdf.command()
        print(f"  Success: command generated")
    except Exception as e:
        print(f"  Error: {e}")