#!/usr/bin/env python3
"""Minimal reproduction of the duplicate segment issue"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/python-http-client_env/lib/python3.13/site-packages')

from python_http_client.client import Client

# Test case that failed
segment1 = '0'
segment2 = '0'

client = Client(host='http://test')

# Access attributes dynamically
child1 = getattr(client, segment1)
child2 = getattr(child1, segment2)

print(f"Segment 1: '{segment1}'")
print(f"Segment 2: '{segment2}'")
print(f"Client URL path: {client._url_path}")
print(f"Child1 URL path: {child1._url_path}")
print(f"Child2 URL path: {child2._url_path}")
print(f"Segment1 index: {child2._url_path.index(segment1) if segment1 in child2._url_path else 'not found'}")
print(f"Segment2 index: {child2._url_path.index(segment2) if segment2 in child2._url_path else 'not found'}")

# Test with different segments
segment3 = 'api'
segment4 = 'v1'

client2 = Client(host='http://test')
child3 = getattr(client2, segment3)
child4 = getattr(child3, segment4)

print(f"\n--- Different segments test ---")
print(f"Segment 3: '{segment3}'")
print(f"Segment 4: '{segment4}'")
print(f"Child4 URL path: {child4._url_path}")
print(f"URL built: {child4._build_url(None)}")