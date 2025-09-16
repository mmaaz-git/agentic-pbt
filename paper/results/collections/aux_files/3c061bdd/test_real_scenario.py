#!/usr/bin/env python3

from flask import Flask, Blueprint

# Test if this bug can occur in real usage
app = Flask(__name__)

# Scenario 1: Blueprint with no prefix, adding empty route
bp1 = Blueprint('api', __name__)

# This is how developers might try to add a root route
try:
    @bp1.route("")  # Empty string route
    def root():
        return "root"
    
    app.register_blueprint(bp1)
    print("✗ UNEXPECTED: Empty route on blueprint without prefix succeeded")
except ValueError as e:
    print(f"✓ EXPECTED: Empty route on blueprint without prefix failed: {e}")

# Scenario 2: Let's check if add_url_rule has the same issue
app2 = Flask(__name__)
bp2 = Blueprint('api2', __name__)

try:
    bp2.add_url_rule("", endpoint="root", view_func=lambda: "root")
    app2.register_blueprint(bp2)
    print("✗ UNEXPECTED: add_url_rule with empty string succeeded")
except ValueError as e:
    print(f"✓ EXPECTED: add_url_rule with empty string failed: {e}")

# Scenario 3: Blueprint with prefix and empty route
app3 = Flask(__name__)
bp3 = Blueprint('api3', __name__, url_prefix="/api")

try:
    @bp3.route("")  # This should work - becomes /api
    def api_root():
        return "api root"
    
    app3.register_blueprint(bp3)
    print("✓ Empty route on blueprint WITH prefix succeeded (becomes /api)")
    
    # Test it works
    with app3.test_client() as client:
        response = client.get("/api")
        print(f"  GET /api -> {response.status_code}")
        
except ValueError as e:
    print(f"✗ Empty route on blueprint with prefix failed: {e}")

print("\n=== CONCLUSION ===")
print("The bug occurs when:")
print("1. A blueprint has no url_prefix (or url_prefix=None)")
print("2. An empty string is used as the route rule")
print("This is a real bug that developers might encounter when trying to")
print("define a root route on a blueprint without a prefix.")