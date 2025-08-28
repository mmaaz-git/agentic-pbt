import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/optax_env/lib/python3.13/site-packages')

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import jax
import jax.numpy as jnp
import optax.monte_carlo as mc

# Test for potential division by zero bug in moving_avg_baseline
def test_moving_avg_baseline_division_by_zero():
    """
    Test moving average baseline with decay=1.0 and zero_debias=True.
    
    When decay=1.0 and zero_debias=True, the update function divides by:
    (1 - decay^(i+1)) = (1 - 1^(i+1)) = (1 - 1) = 0
    
    This should cause a division by zero.
    """
    
    def simple_function(x):
        return float(x[0])
    
    # Create moving average baseline with problematic parameters
    _, _, update_state = mc.moving_avg_baseline(
        simple_function, 
        decay=1.0,  # Problematic value
        zero_debias=True,  # This triggers the division
        use_decay_early_training_heuristic=False  # Ensure decay isn't overridden
    )
    
    # Initialize state
    state = (jnp.array(0.0), 0)  # (value, iteration)
    
    # Create sample
    samples = jnp.array([[10.0]])
    
    # This should trigger the bug
    new_state = update_state(None, samples, state)
    
    # Check if the result is finite
    if not jnp.isfinite(new_state[0]):
        print("BUG FOUND: Division by zero in moving_avg_baseline!")
        print(f"  Parameters: decay=1.0, zero_debias=True")
        print(f"  Result: {new_state[0]} (should be finite)")
        return True
    else:
        print("No bug found in this test")
        return False

if __name__ == "__main__":
    test_moving_avg_baseline_division_by_zero()