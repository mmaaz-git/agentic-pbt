import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pdfkit_env/lib/python3.13/site-packages')

import pdfkit

# Realistic scenario: User accidentally passes a number instead of a string
# This could happen if they're generating HTML content programmatically

page_number = 42
pdf = pdfkit.from_string(page_number, False)  # Should convert 42 to "42"