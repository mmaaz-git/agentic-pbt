"""Reproduce covariance matrix symmetry bug in scipy.odr"""

import numpy as np
import scipy.odr as odr

# Simple model with 7 parameters
def model_func(beta, x):
    result = np.zeros_like(x)
    for i, b in enumerate(beta):
        result += b * (x ** i)
    return result

# Generate data
n_params = 7
n_data = 5
x = np.linspace(0, 1, n_data)
y = np.random.randn(n_data)

# Fit model
model = odr.Model(model_func)
data = odr.Data(x, y)
beta0 = np.ones(n_params)
odr_obj = odr.ODR(data, model, beta0=beta0)
output = odr_obj.run()

# Check if covariance matrix is symmetric
cov_beta = output.cov_beta
print("Covariance matrix shape:", cov_beta.shape)
print("\nCovariance matrix:")
print(cov_beta)
print("\nTranspose of covariance matrix:")
print(cov_beta.T)
print("\nAre they equal?", np.allclose(cov_beta, cov_beta.T))
print("\nMax difference:", np.max(np.abs(cov_beta - cov_beta.T)))

# Check if it's just uninitialized memory
print("\nCovariance matrix contains extreme values suggesting uninitialized memory:")
print("Contains inf:", np.any(np.isinf(cov_beta)))
print("Contains values > 1e100:", np.any(np.abs(cov_beta) > 1e100))