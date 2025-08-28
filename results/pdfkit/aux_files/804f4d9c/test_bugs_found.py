#!/usr/bin/env python3
"""Minimal reproducers for bugs found in pdfkit"""

import sys
import os
import re

# Add the pdfkit package to path
sys.path.insert(0, '/root/hypothesis-llm/envs/pdfkit_env/lib/python3.13/site-packages')

from pdfkit.pdfkit import PDFKit
from pdfkit.configuration import Configuration


# Mock configuration to avoid wkhtmltopdf dependency
class MockConfiguration(Configuration):
    def __init__(self, wkhtmltopdf='mock', meta_tag_prefix='pdfkit-', environ=None):
        self.wkhtmltopdf = wkhtmltopdf
        self.meta_tag_prefix = meta_tag_prefix
        self.environ = environ if environ is not None else os.environ


# Bug 1: Regex injection in meta tag parsing
def demonstrate_regex_injection_bug():
    """Demonstrates regex injection vulnerability in _find_options_in_meta"""
    print("Bug 1: Regex Injection in Meta Tag Parsing")
    print("=" * 50)
    
    # This prefix contains regex special characters
    malicious_prefix = "pdfkit("
    
    html = f'<html><head><meta name="{malicious_prefix}option" content="value"></head></html>'
    
    config = MockConfiguration(meta_tag_prefix=malicious_prefix)
    
    try:
        pdf = PDFKit(html, 'string', configuration=config)
        print("No error - bug not triggered")
    except re.error as e:
        print(f"REGEX ERROR: {e}")
        print(f"Prefix with special regex chars '{malicious_prefix}' causes regex compilation to fail")
        print(f"The code uses: re.search('name=[\"\\']%s' % prefix, x)")
        print(f"Which becomes: re.search('name=[\"\\']pdfkit(', x)")
        print("This is invalid regex due to unmatched parenthesis")
        return True
    
    return False


# Bug 2: Boolean False not converted to empty string
def demonstrate_boolean_bug():
    """Demonstrates boolean False handling bug in _normalize_options"""
    print("\nBug 2: Boolean False Not Converted to Empty String")
    print("=" * 50)
    
    pdf = PDFKit('test', 'string', configuration=MockConfiguration())
    
    # According to line 247: normalized_value = '' if isinstance(value,bool) else value
    # This should convert False to ''
    options = {'test-option': False}
    
    normalized = list(pdf._normalize_options(options))
    
    if normalized:
        key, value = normalized[0]
        print(f"Input: {{'test-option': False}}")
        print(f"Expected value: '' (empty string)")
        print(f"Actual value: {repr(value)}")
        
        if value != '':
            print(f"BUG CONFIRMED: Boolean False returns {repr(value)} instead of empty string")
            print("The bug is in line 247 of pdfkit.py:")
            print("  normalized_value = '' if isinstance(value,bool) else value")
            print("This only converts True to '', but False remains False")
            return True
    
    return False


# Bug 3: Incorrect regex pattern for meta tag extraction
def demonstrate_meta_extraction_bug():
    """Demonstrates incorrect extraction when prefix contains certain characters"""
    print("\nBug 3: Incorrect Meta Tag Extraction with Special Characters")
    print("=" * 50)
    
    # Using '?' in prefix causes incorrect extraction
    prefix = "pdf?"
    option_name = "margin"
    option_value = "10mm"
    
    html = f'<html><head><meta name="{prefix}{option_name}" content="{option_value}"></head></html>'
    
    config = MockConfiguration(meta_tag_prefix=prefix)
    
    # Manually test the regex pattern used in the code
    pattern = 'name=["\']%s([^"\']*)' % prefix
    print(f"Regex pattern: {pattern}")
    print(f"HTML meta tag: <meta name=\"{prefix}{option_name}\" content=\"{option_value}\">")
    
    matches = re.findall(pattern, html)
    print(f"Expected to find: '{option_name}'")
    print(f"Actually found: {matches}")
    
    if matches and matches[0] != option_name:
        print(f"BUG CONFIRMED: Extracted '{matches[0]}' instead of '{option_name}'")
        print("The '?' in the prefix acts as a regex wildcard, matching any character")
        return True
    
    return False


if __name__ == "__main__":
    bugs_found = []
    
    if demonstrate_regex_injection_bug():
        bugs_found.append("Regex Injection")
    
    if demonstrate_boolean_bug():
        bugs_found.append("Boolean Normalization")
    
    if demonstrate_meta_extraction_bug():
        bugs_found.append("Meta Tag Extraction")
    
    print("\n" + "=" * 50)
    print(f"Summary: Found {len(bugs_found)} bugs:")
    for bug in bugs_found:
        print(f"  - {bug}")