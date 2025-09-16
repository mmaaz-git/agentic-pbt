import troposphere
import troposphere.sso as sso

print("Bug: validation=False parameter doesn't bypass title validation")
print("=" * 60)

# Test case 1: Normal validation (should fail)
print("\n1. Creating Application with invalid title ':' and validation=True:")
try:
    app = sso.Application(':', validation=True, Name='test')
    print("   SUCCESS - Created with invalid title")
except ValueError as e:
    print(f"   FAILED - {e}")

# Test case 2: Disabled validation (should succeed but doesn't)  
print("\n2. Creating Application with invalid title ':' and validation=False:")
try:
    app = sso.Application(':', validation=False, Name='test')
    print("   SUCCESS - Created with invalid title")
except ValueError as e:
    print(f"   FAILED - {e}")

# Test case 3: Check what validation=False actually affects
print("\n3. Checking if validation=False affects property validation:")
app = sso.Application('ValidTitle', validation=False, InvalidProperty='test')
print(f"   Created with invalid property 'InvalidProperty': SUCCESS")

print("\n4. Same test with validation=True:")
try:
    app = sso.Application('ValidTitle2', validation=True, InvalidProperty='test')
    print(f"   Created with invalid property 'InvalidProperty': SUCCESS")
except Exception as e:
    print(f"   FAILED - {e}")

print("\n" + "=" * 60)
print("ISSUE: The validation parameter only affects property validation,")
print("       not title validation. Title validation is always enforced.")
print("       This prevents creating resources with non-alphanumeric titles")  
print("       even when validation is explicitly disabled.")