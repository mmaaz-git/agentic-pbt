import requests
import inspect

# Check the Request class
print("Request class hooks initialization:")
print("="*50)

# Create a request object
req = requests.Request('GET', 'http://example.com')
print(f"Default request.hooks type: {type(req.hooks)}")
print(f"Default request.hooks value: {req.hooks}")

# Check PreparedRequest
prepped = req.prepare()
print(f"\nPreparedRequest.hooks type: {type(prepped.hooks)}")
print(f"PreparedRequest.hooks value: {prepped.hooks}")

# Check if we can set hooks to non-dict
print("\n" + "="*50)
print("Testing if hooks can be set to non-dict values:")

# Try setting hooks to a string
req2 = requests.Request('GET', 'http://example.com')
req2.hooks = "not a dict"
prepped2 = req2.prepare()
print(f"After setting to string - PreparedRequest.hooks: {prepped2.hooks}")

# Now let's see what happens if we try to use this in a session
print("\n" + "="*50)
print("Testing with session:")

session = requests.Session()

# Monkey-patch a request to have bad hooks
req3 = requests.Request('GET', 'http://httpbin.org/get')
req3.hooks = "bad hooks"
prepped3 = session.prepare_request(req3)

print(f"PreparedRequest.hooks after session.prepare_request: {prepped3.hooks}")
print(f"Type: {type(prepped3.hooks)}")