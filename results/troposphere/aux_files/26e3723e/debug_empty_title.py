"""Debug why empty title validation is not working."""

import sys
import re
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import certificatemanager

# Test the regex directly
valid_names = re.compile(r"^[a-zA-Z0-9]+$")

print("Testing regex directly:")
print(f"valid_names.match(''): {valid_names.match('')}")
print(f"valid_names.match('Test'): {valid_names.match('Test')}")

print("\nTesting boolean evaluation:")
print(f"bool(''): {bool('')}")
print(f"not '': {not ''}")

print("\nTesting validation condition:")
title = ""
print(f"title = '{title}'")
print(f"not title: {not title}")
print(f"valid_names.match(title): {valid_names.match(title)}")
print(f"not title or not valid_names.match(title): {not title or not valid_names.match(title)}")

print("\nManual validation test:")
if not title or not valid_names.match(title):
    print("SHOULD RAISE ValueError here")
else:
    print("Would NOT raise ValueError")

print("\nChecking if validate_title is called:")

class DebugCertificate(certificatemanager.Certificate):
    def validate_title(self):
        print(f"validate_title called with title='{self.title}'")
        super().validate_title()

try:
    cert = DebugCertificate(title="", DomainName="example.com")
    print("Certificate created successfully")
except ValueError as e:
    print(f"ValueError raised: {e}")