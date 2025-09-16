#!/usr/bin/env python3
"""Minimal reproducer for Bug 2: None title causes TypeError when adding to Template."""

from troposphere import Template
from troposphere.paymentcryptography import Alias

# Create aliases - one with None title, one with valid title
alias1 = Alias(None, AliasName='test-alias-1')
alias2 = Alias('ValidName', AliasName='test-alias-2')

# Add to template
template = Template()
template.add_resource(alias1)
template.add_resource(alias2)

# Try to serialize - this crashes when sorting resources
try:
    json_output = template.to_json()
    print("Unexpectedly succeeded")
except TypeError as e:
    print(f"TypeError: {e}")
    print("\nThe error occurs because None titles bypass validation")
    print("but cause issues when the template tries to sort resources.")