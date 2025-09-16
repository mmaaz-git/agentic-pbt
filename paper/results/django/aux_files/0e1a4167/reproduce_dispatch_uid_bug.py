"""
Investigate dispatch_uid behavior with different senders
"""
from django.dispatch import Signal


def test_dispatch_uid_sender_behavior():
    print("=== Testing dispatch_uid with different senders ===\n")
    
    signal = Signal()
    
    def receiver(sender, **kwargs):
        return "response"
    
    # Test 1: Connect with dispatch_uid and sender=None
    print("Test 1: Connect with dispatch_uid='uid1' and sender=None")
    signal.connect(receiver, sender=None, dispatch_uid="uid1")
    
    # Try to disconnect with same uid but different sender
    print("  Disconnect with dispatch_uid='uid1' and sender=object()")
    result = signal.disconnect(sender=object(), dispatch_uid="uid1")
    print(f"  Result: {result}")
    
    # Check if still connected
    responses = signal.send(sender=None)
    print(f"  Still connected? {len(responses) > 0} (responses: {len(responses)})")
    
    # Clean up
    signal.disconnect(sender=None, dispatch_uid="uid1")
    
    print("\nTest 2: Connect with dispatch_uid and specific sender")
    sender1 = object()
    signal.connect(receiver, sender=sender1, dispatch_uid="uid2")
    
    # Try to disconnect with same uid but different sender
    sender2 = object()
    print(f"  Connected with sender={sender1}")
    print(f"  Disconnect with sender={sender2} and same uid")
    result = signal.disconnect(sender=sender2, dispatch_uid="uid2")
    print(f"  Result: {result}")
    
    # Check if still connected
    responses = signal.send(sender=sender1)
    print(f"  Still connected to sender1? {len(responses) > 0}")


def analyze_lookup_key_logic():
    """Analyze how lookup keys are created."""
    print("\n=== Analyzing lookup_key generation ===\n")
    
    from django.dispatch.dispatcher import _make_id
    
    # Test different scenarios
    scenarios = [
        ("None sender", None),
        ("object() sender", object()),
        ("Same object", object()),
    ]
    
    for name, sender in scenarios:
        sender_id = _make_id(sender)
        print(f"{name}: _make_id() = {sender_id}")
    
    print("\nLooking at the connect() code (line 96-99):")
    print("  if dispatch_uid:")
    print("      lookup_key = (dispatch_uid, _make_id(sender))")
    print("  else:")
    print("      lookup_key = (_make_id(receiver), _make_id(sender))")
    
    print("\nAnd disconnect() code (line 138-141):")
    print("  if dispatch_uid:")
    print("      lookup_key = (dispatch_uid, _make_id(sender))")
    print("  else:")
    print("      lookup_key = (_make_id(receiver), _make_id(sender))")
    
    print("\nBUG: When dispatch_uid is used, the lookup_key includes")
    print("_make_id(sender), so the sender DOES matter even with dispatch_uid!")


def demonstrate_dispatch_uid_bug():
    """Demonstrate the actual bug with dispatch_uid."""
    print("\n=== DEMONSTRATING THE BUG ===\n")
    
    signal = Signal()
    
    def receiver(sender, **kwargs):
        return "response"
    
    # Connect with dispatch_uid and sender=None
    signal.connect(receiver, sender=None, dispatch_uid="my_uid")
    print("Connected: receiver with dispatch_uid='my_uid' and sender=None")
    
    # According to the documentation, dispatch_uid should be enough to identify
    # the connection, but let's try to disconnect with a different sender
    sender = object()
    result = signal.disconnect(sender=sender, dispatch_uid="my_uid")
    
    print(f"\nTried to disconnect with same dispatch_uid but sender=object()")
    print(f"Disconnect returned: {result}")
    
    if result == False:
        print("\nBUG CONFIRMED: dispatch_uid alone is not sufficient to disconnect!")
        print("The sender parameter is incorrectly required to match even when")
        print("dispatch_uid is provided, which defeats the purpose of dispatch_uid")
        
        # Show that we need the exact sender to disconnect
        result2 = signal.disconnect(sender=None, dispatch_uid="my_uid")
        print(f"\nDisconnect with matching sender=None returned: {result2}")
        return True
    
    return False


if __name__ == "__main__":
    test_dispatch_uid_sender_behavior()
    analyze_lookup_key_logic()
    bug_found = demonstrate_dispatch_uid_bug()
    
    if bug_found:
        print("\n" + "="*60)
        print("BUG SUMMARY:")
        print("- dispatch_uid doesn't work as documented")
        print("- The sender parameter matters even when dispatch_uid is provided")
        print("- This makes dispatch_uid less useful for its intended purpose")
        print("- The bug is in how lookup_key includes sender in both cases")
        print("="*60)