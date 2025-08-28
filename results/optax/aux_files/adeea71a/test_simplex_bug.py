import jax.numpy as jnp
import optax.projections as proj
import optax.tree as tree_utils

# Exact failing case from test
tree = {'weights': jnp.array(
         [-172.34867541789822,
          -936.5650557943486,
          184.946864595202,
          1.3960894859440753e-88,
          0.0,
          -0.99999,
          -608.4654932274386,
          290.7272935095816,
          -272.86336024109335,
          447.0993875156528,
          970.1142254640924,
          -5.71617990469855e-251,
          -4.761907845448305e-158,
          691.9887464895105,
          2.183249248285597e-269,
          110.92531735953617,
          999.0,
          442.25964977425724,
          -6.103515625e-05,
          -2.564529500392225e-157,
          -6.386703154551773e-83,
          -509.03445604208775,
          -309.71834735155824,
          585.3156766245925,
          593.7082502138512,
          -7.285996831976411e-212,
          1.2158203238531031e-186,
          0.5,
          -645.8441140625108,
          -3.032459083442255e-72],
     ),
     'bias': 1.1125369292536007e-308}

scale = 49.532750914403536

print('Testing simplex projection idempotence...')
print(f'Scale: {scale}')

once = proj.projection_simplex(tree, scale)
twice = proj.projection_simplex(once, scale)

# Check sums
sum_once = tree_utils.sum(once)
sum_twice = tree_utils.sum(twice)
print(f'\nSum after first projection: {sum_once}')
print(f'Sum after second projection: {sum_twice}')

# Check if sums equal scale
print(f'First sum equals scale? {jnp.allclose(sum_once, scale, rtol=1e-5)}')
print(f'Second sum equals scale? {jnp.allclose(sum_twice, scale, rtol=1e-5)}')

# Check for negative values
def has_negatives(x):
    if isinstance(x, dict):
        for v in x.values():
            if jnp.any(v < -1e-10):
                return True
    else:
        if jnp.any(x < -1e-10):
            return True
    return False

print(f'\nFirst projection has negatives? {has_negatives(once)}')
print(f'Second projection has negatives? {has_negatives(twice)}')

# Check if they're equal
def trees_equal(a, b):
    if isinstance(a, dict):
        for k in a:
            if not jnp.allclose(a[k], b[k], rtol=1e-5, atol=1e-7):
                print(f'  Difference in {k}: {b[k] - a[k]}')
                return False
    else:
        if not jnp.allclose(a, b, rtol=1e-5, atol=1e-7):
            return False
    return True

print(f'\nProjections equal? {trees_equal(once, twice)}')

# Show the values
print('\nFirst projection bias:', once['bias'])
print('Second projection bias:', twice['bias'])
print('Difference in bias:', twice['bias'] - once['bias'])