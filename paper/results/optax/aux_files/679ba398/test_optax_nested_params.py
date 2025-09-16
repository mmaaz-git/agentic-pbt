import jax
import jax.numpy as jnp
import numpy as np
import optax.second_order
from hypothesis import given, strategies as st, settings
import pytest


def test_nested_params_fisher():
    """Test Fisher diagonal with nested parameter structures."""
    # Nested parameter structure (common in neural networks)
    params = {
        'layer1': {'weight': jnp.array([[1.0, 2.0], [3.0, 4.0]]), 
                   'bias': jnp.array([0.1, 0.2])},
        'layer2': {'weight': jnp.array([[0.5]]), 
                   'bias': jnp.array([0.0])}
    }
    
    inputs = jnp.array([[1.0, 2.0], [3.0, 4.0]])
    targets = jnp.array([1.0, 2.0])
    
    def loss_fn(params, inputs, targets):
        # Simple two-layer network
        x = inputs
        x = jnp.dot(x, params['layer1']['weight']) + params['layer1']['bias']
        x = jax.nn.relu(x)
        # For simplicity, just use first column of layer2 weight
        x = jnp.dot(x, params['layer2']['weight'].ravel()) + params['layer2']['bias']
        return jnp.mean((x - targets) ** 2)
    
    # Fisher diagonal should handle nested structures
    fisher = optax.second_order.fisher_diag(loss_fn, params, inputs, targets)
    
    # Result should be flattened
    assert fisher.ndim == 1, f"Fisher should be 1D, got shape {fisher.shape}"
    assert jnp.all(fisher >= 0), "Fisher diagonal should be non-negative"
    assert jnp.all(jnp.isfinite(fisher)), "Fisher diagonal has non-finite values"


def test_nested_params_hvp():
    """Test HVP with nested parameter structures."""
    params = {
        'weight': jnp.array([[1.0, 2.0]]),
        'bias': jnp.array([0.5])
    }
    
    inputs = jnp.array([[1.0, 0.5], [0.5, 1.0]])
    targets = jnp.array([1.5, 2.0])
    
    def loss_fn(params, inputs, targets):
        predictions = jnp.dot(inputs, params['weight'].T).squeeze() + params['bias']
        return jnp.mean((predictions - targets) ** 2)
    
    # Get parameter size
    from jax import flatten_util
    flat_params, unflatten = flatten_util.ravel_pytree(params)
    param_size = flat_params.size
    
    # Test with random vector
    v = jnp.ones(param_size)
    
    hvp_result = optax.second_order.hvp(loss_fn, v, params, inputs, targets)
    
    assert hvp_result.shape == (param_size,), f"HVP shape mismatch: {hvp_result.shape}"
    assert jnp.all(jnp.isfinite(hvp_result)), "HVP has non-finite values"
    
    # Test linearity with nested params
    v2 = jnp.ones(param_size) * 2.0
    hvp2 = optax.second_order.hvp(loss_fn, v2, params, inputs, targets)
    
    # Should be linear
    assert jnp.allclose(hvp2, 2.0 * hvp_result, rtol=1e-6), \
        "HVP linearity violated with nested params"


def test_mixed_dtype_params():
    """Test with mixed precision parameters."""
    # Some params in float32, testing if the functions handle this
    params = jnp.array([1.0, 2.0, 3.0], dtype=jnp.float32)
    inputs = jnp.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], dtype=jnp.float32)
    targets = jnp.array([1.0, 2.0], dtype=jnp.float32)
    
    def loss_fn(p, x, t):
        pred = jnp.dot(x, p)
        return jnp.mean((pred - t) ** 2)
    
    # All functions should work with float32
    fisher = optax.second_order.fisher_diag(loss_fn, params, inputs, targets)
    hess_diag = optax.second_order.hessian_diag(loss_fn, params, inputs, targets)
    hvp_result = optax.second_order.hvp(loss_fn, jnp.ones(3, dtype=jnp.float32), 
                                         params, inputs, targets)
    
    assert fisher.dtype == jnp.float32, f"Fisher dtype mismatch: {fisher.dtype}"
    assert jnp.all(jnp.isfinite(fisher)), "Fisher has non-finite values"
    assert jnp.all(jnp.isfinite(hess_diag)), "Hessian diagonal has non-finite values"
    assert jnp.all(jnp.isfinite(hvp_result)), "HVP has non-finite values"


def test_zero_gradient_case():
    """Test when gradient is zero (at a critical point)."""
    params = jnp.array([0.0, 0.0])
    inputs = jnp.array([[1.0, -1.0], [1.0, -1.0]])  # Symmetric inputs
    targets = jnp.array([0.0, 0.0])  # Targets that make gradient zero
    
    def loss_fn(p, x, t):
        pred = jnp.dot(x, p)
        return jnp.mean((pred - t) ** 2)
    
    # At this point, gradient should be zero
    grad = jax.grad(loss_fn)(params, inputs, targets)
    assert jnp.allclose(grad, 0.0, atol=1e-8), f"Gradient not zero: {grad}"
    
    # Fisher diagonal should be zero when gradient is zero
    fisher = optax.second_order.fisher_diag(loss_fn, params, inputs, targets)
    assert jnp.allclose(fisher, 0.0, atol=1e-10), f"Fisher not zero: {fisher}"
    
    # Hessian diagonal and HVP should still be well-defined
    hess_diag = optax.second_order.hessian_diag(loss_fn, params, inputs, targets)
    hvp_result = optax.second_order.hvp(loss_fn, jnp.ones(2), params, inputs, targets)
    
    assert jnp.all(jnp.isfinite(hess_diag)), "Hessian diagonal has non-finite values"
    assert jnp.all(jnp.isfinite(hvp_result)), "HVP has non-finite values"


def test_single_parameter():
    """Test with a single scalar parameter."""
    params = jnp.array(2.0)  # Single scalar parameter
    inputs = jnp.array([[1.0], [2.0], [3.0]])
    targets = jnp.array([2.0, 4.0, 6.0])
    
    def loss_fn(p, x, t):
        pred = x.squeeze() * p
        return jnp.mean((pred - t) ** 2)
    
    # Should work with scalar parameters
    fisher = optax.second_order.fisher_diag(loss_fn, params, inputs, targets)
    hess_diag = optax.second_order.hessian_diag(loss_fn, params, inputs, targets)
    hvp_result = optax.second_order.hvp(loss_fn, jnp.array(1.0), params, inputs, targets)
    
    # Results should be scalar or 1-element arrays
    assert fisher.size == 1, f"Fisher size should be 1, got {fisher.size}"
    assert hess_diag.size == 1, f"Hessian diagonal size should be 1, got {hess_diag.size}"
    assert hvp_result.size == 1, f"HVP size should be 1, got {hvp_result.size}"
    
    assert jnp.all(jnp.isfinite(fisher)), "Fisher has non-finite values"
    assert jnp.all(jnp.isfinite(hess_diag)), "Hessian diagonal has non-finite values"
    assert jnp.all(jnp.isfinite(hvp_result)), "HVP has non-finite values"


if __name__ == "__main__":
    print("Running nested parameter structure tests...")
    
    print("\n1. Testing nested params with Fisher...")
    test_nested_params_fisher()
    
    print("\n2. Testing nested params with HVP...")
    test_nested_params_hvp()
    
    print("\n3. Testing mixed dtype params...")
    test_mixed_dtype_params()
    
    print("\n4. Testing zero gradient case...")
    test_zero_gradient_case()
    
    print("\n5. Testing single parameter...")
    test_single_parameter()
    
    print("\nAll nested parameter tests completed!")