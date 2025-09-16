"""Minimal reproduction of URL path round-trip bug."""

from hypothesis import given, strategies as st, settings
from pydantic.networks import HttpUrl, AnyUrl


@given(st.just(None))
@settings(max_examples=1)
def test_url_path_round_trip_bug(path):
    """
    Test that demonstrates the URL path round-trip bug.
    
    When building a URL with path=None, the resulting URL has path='/'.
    But when rebuilding with path='/', the URL gets path='//' causing a mismatch.
    """
    # Build original URL with path=None
    original = HttpUrl.build(
        scheme='http',
        host='example.com',
        path=path
    )
    
    # Extract the path (will be '/')
    extracted_path = original.path
    
    # Rebuild with extracted path
    rebuilt = HttpUrl.build(
        scheme='http',
        host='example.com',
        path=extracted_path
    )
    
    # These should be equal but they're not
    print(f"Original: {original} (path={repr(original.path)})")
    print(f"Rebuilt:  {rebuilt} (path={repr(rebuilt.path)})")
    print(f"Match: {str(original) == str(rebuilt)}")
    
    assert str(original) == str(rebuilt), f"{str(original)} != {str(rebuilt)}"


if __name__ == "__main__":
    test_url_path_round_trip_bug()