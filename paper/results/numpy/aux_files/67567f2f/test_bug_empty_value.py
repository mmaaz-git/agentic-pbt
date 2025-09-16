from requests.cookies import RequestsCookieJar

def test_empty_string_value_bug():
    jar = RequestsCookieJar()
    
    # Set a cookie with empty string value
    jar.set('test', '')
    
    # The cookie exists in the jar
    for cookie in jar:
        if cookie.name == 'test':
            print(f"Cookie exists with value: {repr(cookie.value)}")
            assert cookie.value == ''
    
    # But get() returns None instead of empty string
    result = jar.get('test')
    print(f"jar.get('test') returns: {repr(result)}")
    
    # This is a bug - it should return '' not None
    # The cookie has value '', so get() should return ''
    assert result == '', f"Expected '', got {repr(result)}"

if __name__ == "__main__":
    test_empty_string_value_bug()