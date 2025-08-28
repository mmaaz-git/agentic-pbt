from flask.views import MethodView

# Dynamically create a MethodView class
def create_view_with_methods(methods):
    class DynamicView(MethodView):
        pass
    
    # Add methods dynamically
    for method in methods:
        setattr(DynamicView, method, lambda self: f"{method} response")
    
    return DynamicView

# Create a view with GET and POST methods
ViewClass = create_view_with_methods(['get', 'post'])

# Check if methods attribute is set
print(f"ViewClass.methods: {ViewClass.methods}")
print(f"Expected: {{'GET', 'POST'}}")

# The methods attribute should be {'GET', 'POST'} but it's None
# because __init_subclass__ was called before the methods were added