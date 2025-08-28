import flask
import flask.ctx
import traceback

app = flask.Flask('test')

print("Testing context corruption after wrong pop...")
print("=" * 50)

# Create two contexts
ctx1 = flask.ctx.AppContext(app)
ctx2 = flask.ctx.AppContext(app)

print("1. Pushing ctx1...")
ctx1.push()
print(f"   has_app_context: {flask.ctx.has_app_context()}")

print("\n2. Pushing ctx2...")
ctx2.push()
print(f"   has_app_context: {flask.ctx.has_app_context()}")

print("\n3. Attempting to pop ctx1 (wrong order)...")
try:
    ctx1.pop()
    print("   ERROR: Should have raised AssertionError!")
except AssertionError as e:
    print(f"   Got expected AssertionError: {e}")
    
print("\n4. Checking context state after failed pop...")
print(f"   has_app_context: {flask.ctx.has_app_context()}")

print("\n5. Attempting to pop ctx2 (should be on top)...")
try:
    ctx2.pop()
    print("   Successfully popped ctx2")
except LookupError as e:
    print(f"   ERROR: Got LookupError: {e}")
    print("   The context stack is corrupted!")
    traceback.print_exc()
    
print("\n6. Final context state...")
print(f"   has_app_context: {flask.ctx.has_app_context()}")

print("\n" + "=" * 50)
print("CONCLUSION: After a failed pop due to wrong order,")
print("the context stack becomes corrupted and cannot be")
print("properly cleaned up. This is a bug!")