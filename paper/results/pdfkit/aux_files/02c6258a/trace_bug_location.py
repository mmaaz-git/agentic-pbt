import sys
import traceback
sys.path.insert(0, '/root/hypothesis-llm/envs/pdfkit_env/lib/python3.13/site-packages')

from pdfkit.pdfkit import PDFKit

# Mock configuration 
class MockConfig:
    def __init__(self):
        self.wkhtmltopdf = '/usr/bin/wkhtmltopdf'
        self.meta_tag_prefix = 'pdfkit-'
        self.environ = {}

print("Tracing exact failure location when non-string passed to PDFKit...")
print("-" * 60)

try:
    # This should work if the code properly handled type conversion
    pdf = PDFKit(42, 'string', configuration=MockConfig())
    cmd = pdf.command()
except Exception as e:
    print("Full traceback:")
    traceback.print_exc()
    print("\n" + "=" * 60)
    print("Summary: The bug occurs when _find_options_in_meta is called")
    print("on non-string input during PDFKit initialization.")
    print("The regex operations expect a string but get other types.")