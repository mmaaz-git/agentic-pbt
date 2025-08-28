import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.devopsguru import NotificationChannel, NotificationChannelConfig, SnsChannelConfig

# Test cases of characters that Python considers alphanumeric but troposphere rejects
test_cases = [
    'µ',        # Greek letter mu
    'ñame',     # Spanish n with tilde
    'café',     # French e with accent
    'αβγ',      # Greek letters
    '你好',     # Chinese characters
    'naïve',    # i with diaeresis
    'Müller',   # German u with umlaut
    'José',     # Spanish name with accent
]

config = NotificationChannelConfig(Sns=SnsChannelConfig(TopicArn="arn:aws:sns:us-east-1:123456789012:test"))

print("Testing title validation bug:")
print("=" * 60)

for title in test_cases:
    is_alnum = title.isalnum()
    try:
        nc = NotificationChannel(title, Config=config)
        nc.to_dict()
        result = "ACCEPTED"
    except ValueError as e:
        if 'not alphanumeric' in str(e):
            result = "REJECTED (claims 'not alphanumeric')"
        else:
            result = f"REJECTED ({e})"
    
    print(f"Title: {title:15} | Python isalnum(): {is_alnum:5} | Troposphere: {result}")
    
    # Verify the bug: if Python says it's alphanumeric but troposphere says it's not
    if is_alnum and "not alphanumeric" in result:
        print(f"  ⚠️  BUG: '{title}' IS alphanumeric by Python standards but error says it's not!")

print("\nConclusion: The error message 'not alphanumeric' is misleading.")
print("The code actually only accepts ASCII letters and digits [a-zA-Z0-9],")
print("but the error message implies it checks for general alphanumeric characters.")