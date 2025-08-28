import inspect
import requests.api


def test_json_parameter_signature_inconsistency():
    """Test that demonstrates the API inconsistency in how json parameter is handled.
    
    POST explicitly lists json in its signature, while PUT and PATCH don't,
    even though all three document accepting json parameter and commonly need it.
    """
    
    # Get the signatures
    post_sig = inspect.signature(requests.api.post)
    put_sig = inspect.signature(requests.api.put)
    patch_sig = inspect.signature(requests.api.patch)
    
    # Check if 'json' is in the explicit parameters
    post_params = list(post_sig.parameters.keys())
    put_params = list(put_sig.parameters.keys())
    patch_params = list(patch_sig.parameters.keys())
    
    print("POST parameters:", post_params)
    print("PUT parameters:", put_params)
    print("PATCH parameters:", patch_params)
    
    # POST has json as explicit parameter
    assert 'json' in post_params, "POST should have json parameter"
    
    # PUT and PATCH don't have json as explicit parameter (even though docs say they do)
    assert 'json' not in put_params, "PUT doesn't have json as explicit parameter"
    assert 'json' not in patch_params, "PATCH doesn't have json as explicit parameter"
    
    # But all three claim to accept json in their docstrings
    assert 'json:' in requests.api.post.__doc__, "POST documents json parameter"
    assert 'json:' in requests.api.put.__doc__, "PUT documents json parameter"
    assert 'json:' in requests.api.patch.__doc__, "PATCH documents json parameter"
    
    print("\nInconsistency found:")
    print("- POST has 'json' as an explicit parameter in signature")
    print("- PUT and PATCH don't have 'json' in signature, only in **kwargs")
    print("- All three document accepting 'json' parameter in docstrings")
    print("\nThis creates an inconsistent API where functionally equivalent methods")
    print("(POST, PUT, PATCH all commonly send JSON data) have different signatures.")


if __name__ == "__main__":
    test_json_parameter_signature_inconsistency()