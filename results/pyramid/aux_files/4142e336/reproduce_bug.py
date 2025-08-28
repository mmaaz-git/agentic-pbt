"""Minimal reproduction of the Unicode encoding bug in pyramid.request.call_app_with_subpath_as_path_info"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from unittest.mock import Mock
from pyramid.request import call_app_with_subpath_as_path_info

# Create a request with Unicode character in subpath
request = Mock()
request.subpath = ['€', 'page']  # Euro sign (U+20AC) cannot be encoded to latin-1
request.environ = {
    'SCRIPT_NAME': '',
    'PATH_INFO': '/€/page'
}

new_request = Mock()
new_request.environ = {}
new_request.get_response = Mock(return_value="response")
request.copy = Mock(return_value=new_request)

app = Mock()

# This will raise UnicodeEncodeError
call_app_with_subpath_as_path_info(request, app)