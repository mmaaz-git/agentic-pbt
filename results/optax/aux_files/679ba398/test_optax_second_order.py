import jax
import jax.numpy as jnp
import numpy as np
import optax.second_order
from hypothesis import given, strategies as st, assume, settings
import pytest
import math


# Custom strategies for JAX arrays and model parameters
@st.composite
def jax_arrays(draw, shape=(2, 3), min_value=-10, max_value=10):
    """Generate JAX arrays with reasonable values."""
    arr = draw(st.lists(
        st.floats(min_value=min_value, max_value=max_value, 
                  allow_nan=False, allow_infinity=False),
        min_size=int(np.prod(shape)), max_size=int(np.prod(shape))
    ))
    return jnp.array(arr).reshape(shape)


@st.composite  
def simple_params(draw, param_size=3):
    """Generate simple parameter vectors."""
    params = draw(st.lists(
        st.floats(min_value=-5, max_value=5,
                  allow_nan=False, allow_infinity=False),
        min_size=param_size, max_size=param_size
    ))
    return jnp.array(params)


@st.composite
def loss_inputs(draw, batch_size=2, input_dim=3, param_dim=3):
    """Generate consistent loss function inputs."""
    params = draw(simple_params(param_dim))
    inputs = draw(jax_arrays((batch_size, input_dim), -5, 5))
    targets = draw(jax_arrays((batch_size,), -5, 5))
    return params, inputs, targets


def quadratic_loss(params, inputs, targets):
    """Simple quadratic loss for testing."""
    # Reshape params to match input dimensions if needed
    param_flat = params.ravel()
    if param_flat.size >= inputs.shape[1]:
        weight = param_flat[:inputs.shape[1]]
        predictions = jnp.dot(inputs, weight)
    else:
        # Pad params with zeros if too small
        weight = jnp.pad(param_flat, (0, inputs.shape[1] - param_flat.size))
        predictions = jnp.dot(inputs, weight)
    return jnp.mean((predictions - targets) ** 2)


def negative_log_likelihood(params, inputs, targets):
    """Simple negative log likelihood for testing Fisher diagonal."""
    # Reshape params to match input dimensions if needed
    param_flat = params.ravel()
    if param_flat.size >= inputs.shape[1]:
        weight = param_flat[:inputs.shape[1]]
        logits = jnp.dot(inputs, weight)
    else:
        # Pad params with zeros if too small
        weight = jnp.pad(param_flat, (0, inputs.shape[1] - param_flat.size))
        logits = jnp.dot(inputs, weight)
    return jnp.mean((logits - targets) ** 2)  # Simplified NLL


# Test 1: Fisher diagonal non-negativity
@given(loss_inputs())
@settings(max_examples=100)
def test_fisher_diagonal_non_negative(loss_input):
    params, inputs, targets = loss_input
    
    fisher = optax.second_order.fisher_diag(
        negative_log_likelihood, params, inputs, targets
    )
    
    # All Fisher diagonal elements must be non-negative (they are squares)
    assert jnp.all(fisher >= 0), f"Found negative Fisher diagonal values: {fisher[fisher < 0]}"


# Test 2: HVP linearity
@given(loss_inputs(), st.floats(min_value=-2, max_value=2, allow_nan=False, allow_infinity=False),
       st.floats(min_value=-2, max_value=2, allow_nan=False, allow_infinity=False))
@settings(max_examples=100)
def test_hvp_linearity(loss_input, alpha, beta):
    params, inputs, targets = loss_input
    param_size = params.ravel().size
    
    # Generate two random vectors
    v1 = jnp.ones(param_size) * 0.1
    v2 = jnp.ones(param_size) * -0.1
    
    # Linear combination
    v_combined = alpha * v1 + beta * v2
    
    # Compute HVPs
    hvp1 = optax.second_order.hvp(quadratic_loss, v1, params, inputs, targets)
    hvp2 = optax.second_order.hvp(quadratic_loss, v2, params, inputs, targets)
    hvp_combined = optax.second_order.hvp(quadratic_loss, v_combined, params, inputs, targets)
    
    expected = alpha * hvp1 + beta * hvp2
    
    # Check linearity property
    assert jnp.allclose(hvp_combined, expected, rtol=1e-5, atol=1e-7), \
        f"HVP linearity violated: max diff = {jnp.max(jnp.abs(hvp_combined - expected))}"


# Test 3: HVP with zero vector
@given(loss_inputs())
@settings(max_examples=100)
def test_hvp_zero_vector(loss_input):
    params, inputs, targets = loss_input
    param_size = params.ravel().size
    
    # Zero vector
    v_zero = jnp.zeros(param_size)
    
    # HVP with zero should be zero
    result = optax.second_order.hvp(quadratic_loss, v_zero, params, inputs, targets)
    
    assert jnp.allclose(result, 0, atol=1e-8), \
        f"HVP with zero vector is not zero: {result}"


# Test 4: Hessian symmetry via HVP
@given(loss_inputs(param_dim=2))  # Small dimension for efficiency
@settings(max_examples=50)
def test_hessian_symmetry_via_hvp(loss_input):
    params, inputs, targets = loss_input
    param_size = params.ravel().size
    
    # Pick two indices to test symmetry
    for i in range(min(param_size, 3)):
        for j in range(i+1, min(param_size, 3)):
            # Standard basis vectors
            ei = jnp.zeros(param_size).at[i].set(1.0)
            ej = jnp.zeros(param_size).at[j].set(1.0)
            
            # Compute H*ei and H*ej
            h_ei = optax.second_order.hvp(quadratic_loss, ei, params, inputs, targets)
            h_ej = optax.second_order.hvp(quadratic_loss, ej, params, inputs, targets)
            
            # Check symmetry: (H*ei)[j] == (H*ej)[i]
            assert jnp.allclose(h_ei[j], h_ej[i], rtol=1e-5, atol=1e-7), \
                f"Hessian not symmetric: H[{i},{j}]={h_ei[j]} != H[{j},{i}]={h_ej[i]}"


# Test 5: Hessian diagonal consistency  
@given(loss_inputs(param_dim=3))
@settings(max_examples=50, deadline=10000)  # Increased deadline for slower computation
def test_hessian_diagonal_consistency(loss_input):
    params, inputs, targets = loss_input
    param_size = params.ravel().size
    
    # Get diagonal via hessian_diag function
    diag_direct = optax.second_order.hessian_diag(quadratic_loss, params, inputs, targets)
    
    # Get diagonal via HVP with standard basis vectors
    diag_via_hvp = []
    for i in range(param_size):
        ei = jnp.zeros(param_size).at[i].set(1.0)
        h_ei = optax.second_order.hvp(quadratic_loss, ei, params, inputs, targets)
        diag_via_hvp.append(h_ei[i])
    diag_via_hvp = jnp.array(diag_via_hvp)
    
    # They should match
    assert jnp.allclose(diag_direct, diag_via_hvp, rtol=1e-4, atol=1e-6), \
        f"Diagonal mismatch: direct={diag_direct}, via_hvp={diag_via_hvp}"


if __name__ == "__main__":
    # Run tests
    print("Running property-based tests for optax.second_order...")
    
    print("\n1. Testing Fisher diagonal non-negativity...")
    test_fisher_diagonal_non_negative()
    
    print("\n2. Testing HVP linearity...")
    test_hvp_linearity()
    
    print("\n3. Testing HVP with zero vector...")
    test_hvp_zero_vector()
    
    print("\n4. Testing Hessian symmetry...")
    test_hessian_symmetry_via_hvp()
    
    print("\n5. Testing Hessian diagonal consistency...")
    test_hessian_diagonal_consistency()
    
    print("\nAll tests completed!")