import urllib.robotparser

# Real-world scenario: paths with special characters
parser = urllib.robotparser.RobotFileParser()

robots_txt = """
User-agent: *
Disallow: /api:v2/
Disallow: /search?q=test
"""

parser.parse(robots_txt.splitlines())

# Check what paths are stored
for entry in parser.entries + ([parser.default_entry] if parser.default_entry else []):
    for rule in entry.rulelines:
        print(f"Stored path: {rule.path!r}, Allow: {rule.allowance}")

print("\nTesting access:")
print(f"Can fetch '/api:v2/test'? {parser.can_fetch('bot', '/api:v2/test')}")
print(f"Can fetch '/api%3Av2/test'? {parser.can_fetch('bot', '/api%3Av2/test')}")
print(f"Can fetch '/search?q=test'? {parser.can_fetch('bot', '/search?q=test')}")

print("\n--- Double encoding demonstration ---")
# If we programmatically create rules from parsed rules
original_rule = urllib.robotparser.RuleLine('/test:path', False)
print(f"Original: path='/test:path' -> {original_rule.path!r}")

# Simulating re-processing (e.g., serializing and re-parsing)
reprocessed_rule = urllib.robotparser.RuleLine(original_rule.path, False)
print(f"Reprocessed: path='{original_rule.path}' -> {reprocessed_rule.path!r}")

# They should match the same URLs but don't
test_url = '/test%3Apath'
print(f"\nDoes original match '{test_url}'? {original_rule.applies_to(test_url)}")
print(f"Does reprocessed match '{test_url}'? {reprocessed_rule.applies_to(test_url)}")