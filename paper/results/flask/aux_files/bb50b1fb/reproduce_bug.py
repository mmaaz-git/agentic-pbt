#!/usr/bin/env python3
"""Minimal reproduction of access_control_allow_methods bug."""

from flask import Response

# Bug: Setting access_control_allow_methods as a string incorrectly 
# treats each character as a separate method

response = Response()
response.access_control_allow_methods = "GET"

# Expected: HeaderSet(['GET'])
# Actual: HeaderSet(['G', 'E', 'T'])
print(f"Setting 'GET' results in: {response.access_control_allow_methods}")
print(f"Raw header value: {response.headers.get('Access-Control-Allow-Methods')}")

# This shows the bug more clearly
response2 = Response()
response2.access_control_allow_methods = "POST"
print(f"\nSetting 'POST' results in: {response2.access_control_allow_methods}")

# The workaround is to use a list
response3 = Response()
response3.access_control_allow_methods = ["GET", "POST"] 
print(f"\nUsing list ['GET', 'POST'] works correctly: {response3.access_control_allow_methods}")