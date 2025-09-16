"""Minimal reproduction of the Tags type validation bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.codeartifact as codeartifact

# This is what users might naturally try based on CloudFormation documentation
# CloudFormation accepts Tags as a list of key-value pairs
try:
    domain = codeartifact.Domain(
        title="TestDomain",
        DomainName="my-domain",
        Tags=[{"Key": "Environment", "Value": "Production"}]
    )
    print("SUCCESS: Domain created with list of tag dicts")
except TypeError as e:
    print(f"FAILED: {e}")

# This is what the library actually requires
from troposphere import Tags

domain2 = codeartifact.Domain(
    title="TestDomain2", 
    DomainName="my-domain2",
    Tags=Tags({"Environment": "Production"})
)
print("SUCCESS: Domain created with Tags object")

# The issue: The library's type checking is too strict
# It requires the Tags class but CloudFormation templates commonly use lists