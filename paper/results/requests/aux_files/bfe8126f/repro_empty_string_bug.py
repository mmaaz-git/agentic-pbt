from requests.cookies import RequestsCookieJar, cookiejar_from_dict

# Bug 1: Empty string cookie values are lost
jar = RequestsCookieJar()
jar.set('test', '')
print(f"Set cookie 'test' to empty string")
print(f"jar.get('test') returns: {jar.get('test')!r}")
print(f"Expected: '' but got: {jar.get('test')!r}")

# Also happens with dict operations
jar2 = RequestsCookieJar()
jar2['name'] = ''
try:
    result = jar2['name']
    print(f"\njar2['name'] returns: {result!r}")
except KeyError as e:
    print(f"\njar2['name'] raises KeyError: {e}")

# And with cookiejar_from_dict
jar3 = cookiejar_from_dict({'key': ''})
print(f"\nCreated jar from dict {{'key': ''}}")
print(f"jar3.get('key') returns: {jar3.get('key')!r}")
print(f"Expected: '' but got: {jar3.get('key')!r}")