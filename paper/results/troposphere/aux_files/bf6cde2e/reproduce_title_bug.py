#!/usr/bin/env python3
"""Minimal reproduction of title validation bypass bug in troposphere"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import Template
from troposphere.mediaconvert import JobTemplate

# Bug 1: Empty string bypasses validation
jt_empty = JobTemplate("", SettingsJson={"key": "value"})
print(f"Created JobTemplate with empty title: {jt_empty.title!r}")

# Bug 2: None bypasses validation  
jt_none = JobTemplate(None, SettingsJson={"key": "value"})
print(f"Created JobTemplate with None title: {jt_none.title!r}")

# Bug 3: These invalid titles can be added to CloudFormation templates
template = Template()
jt_in_template = JobTemplate("", template=template, SettingsJson={})
print(f"Added resource with empty title to template: {'' in template.resources}")

# Bug 4: Serialization works with invalid titles
cf_json = template.to_json()
print(f"Template serializes with empty-titled resource")

# The regex clearly requires at least one character
import troposphere
print(f"\nRegex pattern: {troposphere.valid_names.pattern}")
print(f"Empty string should match: {bool(troposphere.valid_names.match(''))}")
print(f"The validation is skipped due to: if self.title: self.validate_title()")