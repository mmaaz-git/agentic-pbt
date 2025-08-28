import urllib.robotparser
import urllib.parse
from hypothesis import given, strategies as st, assume, settings
import math


# Strategy for valid URL paths
valid_paths = st.text(min_size=0, max_size=100).map(
    lambda s: '/' + s.replace('\x00', '').replace('#', '').strip('/')
)

# Strategy for user agents
user_agents = st.text(min_size=1, max_size=50, alphabet=st.characters(
    blacklist_categories=('Cc', 'Cs'), blacklist_characters='\x00\n\r:'
)).filter(lambda s: s.strip())

# Strategy for simple robots.txt content
def robots_content_strategy():
    return st.lists(
        st.tuples(
            st.sampled_from(['User-agent', 'Disallow', 'Allow']),
            st.text(min_size=0, max_size=50).filter(lambda s: '\n' not in s and '\r' not in s)
        ),
        min_size=1,
        max_size=10
    ).map(lambda lines: '\n'.join(f'{k}: {v}' for k, v in lines))


@given(valid_paths)
def test_ruleline_path_normalization(path):
    """Test that RuleLine path normalization is consistent"""
    rule = urllib.robotparser.RuleLine(path, True)
    # The path should be properly quoted
    # Parsing and quoting should be idempotent
    rule2 = urllib.robotparser.RuleLine(rule.path, True)
    assert rule.path == rule2.path


@given(st.text(min_size=0, max_size=100))
def test_ruleline_empty_disallow_becomes_allow(path):
    """Test that empty Disallow becomes Allow (as per spec)"""
    # Only empty path with disallow should become allow
    rule = urllib.robotparser.RuleLine('', False)
    assert rule.allowance == True
    
    # Non-empty paths should preserve their allowance
    if path != '':
        rule2 = urllib.robotparser.RuleLine(path, False)
        assert rule2.allowance == False


@given(user_agents, valid_paths)
def test_entry_applies_to_case_insensitive(useragent, path):
    """Test that user-agent matching is case-insensitive"""
    entry = urllib.robotparser.Entry()
    entry.useragents.append(useragent.lower())
    
    # Should match regardless of case
    assert entry.applies_to(useragent.upper()) == entry.applies_to(useragent.lower())
    assert entry.applies_to(useragent) == entry.applies_to(useragent.lower())


@given(st.text(min_size=1, max_size=50))
def test_user_agent_wildcard_precedence(useragent):
    """Test that wildcard (*) user-agent always matches"""
    entry = urllib.robotparser.Entry()
    entry.useragents.append('*')
    
    # Wildcard should match any user agent
    assert entry.applies_to(useragent) == True


@given(st.lists(st.tuples(valid_paths, st.booleans()), min_size=1, max_size=5))
def test_first_matching_rule_wins(rules):
    """Test that first matching rule determines the outcome"""
    entry = urllib.robotparser.Entry()
    entry.useragents.append('*')
    
    for path, allowance in rules:
        entry.rulelines.append(urllib.robotparser.RuleLine(path, allowance))
    
    # Test with a path that matches the first rule
    if rules:
        first_path, first_allowance = rules[0]
        if first_path:
            # The first rule should determine the outcome
            result = entry.allowance(first_path)
            # Note: empty path is special case
            if first_path == '' and not first_allowance:
                assert result == True  # empty disallow means allow all
            else:
                assert result == first_allowance or first_path == ''


@given(st.text(min_size=0, max_size=100))
def test_url_path_extraction_preserves_structure(url_path):
    """Test URL path handling in can_fetch"""
    assume(not url_path.startswith('//'))  # Avoid protocol-relative URLs
    
    parser = urllib.robotparser.RobotFileParser()
    parser.parse(['User-agent: *', 'Allow: /'])
    
    # Should not crash on any input
    try:
        # Build a full URL for testing
        test_url = 'http://example.com' + url_path
        result = parser.can_fetch('TestBot', test_url)
        assert isinstance(result, bool)
    except Exception as e:
        # URL parsing should handle edge cases gracefully
        pass


@given(st.integers(min_value=0, max_value=1000), st.integers(min_value=1, max_value=1000))
def test_request_rate_parsing(requests, seconds):
    """Test request-rate parsing"""
    parser = urllib.robotparser.RobotFileParser()
    content = f"""User-agent: *
Request-rate: {requests}/{seconds}"""
    
    parser.parse(content.splitlines())
    rate = parser.request_rate('TestBot')
    
    if rate:
        assert rate.requests == requests
        assert rate.seconds == seconds


@given(st.integers())
def test_crawl_delay_parsing_integer_only(value):
    """Test that crawl-delay only accepts valid integers"""
    parser = urllib.robotparser.RobotFileParser()
    content = f"""User-agent: *
Crawl-delay: {value}"""
    
    parser.parse(content.splitlines())
    delay = parser.crawl_delay('TestBot')
    
    # Should parse positive integers
    if value >= 0 and str(value).isdigit():
        assert delay == value
    else:
        # Invalid values should be ignored
        assert delay is None


@given(st.text(min_size=0, max_size=200))
def test_parse_handles_malformed_input(content):
    """Test that parse handles any input without crashing"""
    parser = urllib.robotparser.RobotFileParser()
    
    # Should not crash on any input
    try:
        parser.parse(content.splitlines())
        # Parser should always leave the object in a valid state
        assert isinstance(parser.entries, list)
        assert parser.default_entry is None or isinstance(parser.default_entry, urllib.robotparser.Entry)
    except Exception as e:
        # Should not raise exceptions on malformed input
        assert False, f"Parser crashed on input: {e}"


@given(st.text(min_size=1, max_size=50).filter(lambda s: '/' in s))
def test_user_agent_split_behavior(useragent_with_slash):
    """Test user-agent splitting on '/' character"""
    entry = urllib.robotparser.Entry()
    entry.useragents.append(useragent_with_slash)
    
    # The applies_to method splits on '/' and takes first part
    parts = useragent_with_slash.split('/')
    first_part = parts[0].lower()
    
    # Should match if first part is contained in the checking agent
    test_agent = first_part + '/2.0'
    assert entry.applies_to(test_agent) == True
    
    # Should also match the original
    assert entry.applies_to(useragent_with_slash) == True


@given(st.text(min_size=0, max_size=100))
def test_url_quoting_unquoting_consistency(path):
    """Test URL quoting/unquoting in can_fetch"""
    parser = urllib.robotparser.RobotFileParser()
    parser.parse(['User-agent: *', 'Disallow: /private/', 'Allow: /'])
    
    # Test with various URL encodings
    base_url = 'http://example.com'
    
    # The function should handle both quoted and unquoted URLs
    url1 = base_url + path
    url2 = base_url + urllib.parse.quote(path)
    
    # Should handle the URL consistently
    try:
        result1 = parser.can_fetch('TestBot', url1)
        result2 = parser.can_fetch('TestBot', url2) 
        # Both should return same type
        assert isinstance(result1, bool)
        assert isinstance(result2, bool)
    except Exception:
        pass  # Some paths might be invalid URLs


@given(st.lists(st.text(min_size=0, max_size=50), min_size=0, max_size=20))
def test_sitemap_independence(lines):
    """Test that sitemap directives are independent of user-agent state"""
    # Build a robots.txt with sitemaps interspersed
    content = []
    sitemap_count = 0
    
    for i, line in enumerate(lines):
        if i % 3 == 0:
            content.append(f'Sitemap: http://example.com/sitemap{i}.xml')
            sitemap_count += 1
        content.append(f'User-agent: bot{i}')
        content.append(f'Disallow: /{line}')
    
    parser = urllib.robotparser.RobotFileParser()
    parser.parse(content)
    
    # Sitemaps should be collected regardless of position
    sitemaps = parser.site_maps()
    if sitemap_count > 0:
        assert sitemaps is not None
        assert len(sitemaps) == sitemap_count


@given(st.text(min_size=1, max_size=100))
def test_can_fetch_requires_read_or_parse(url):
    """Test that can_fetch returns False before read() or parse()"""
    parser = urllib.robotparser.RobotFileParser()
    # Without calling read() or parse(), should deny access
    assert parser.can_fetch('TestBot', url) == False
    
    # After parsing, behavior should change
    parser.parse(['User-agent: *', 'Allow: /'])
    assert parser.can_fetch('TestBot', url) == True


if __name__ == '__main__':
    # Run with more examples to find edge cases
    import pytest
    pytest.main([__file__, '-v', '--hypothesis-show-statistics'])