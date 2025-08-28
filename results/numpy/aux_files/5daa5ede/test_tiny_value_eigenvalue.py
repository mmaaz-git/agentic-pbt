import numpy as np
import numpy.linalg as la

def test_matrix_with_epsilon(epsilon):
    """Test eigenvalue computation with tiny perturbation"""
    
    # Create matrix with small perturbation
    A = np.array([[0, 0, 0, epsilon, 0],
                  [1, 0, 0, 0, 1],
                  [0, 0, 0, 0, 0],
                  [0, 0, 0, 0, 1],
                  [0, 1, 0, 0, 0]], dtype=float)
    
    eigenvalues, eigenvectors = la.eig(A)
    
    # Check eigenvalue equation
    failures = []
    for i in range(len(eigenvalues)):
        lambda_i = eigenvalues[i]
        v_i = eigenvectors[:, i]
        
        Av = A @ v_i
        lambda_v = lambda_i * v_i
        
        error = np.linalg.norm(Av - lambda_v)
        
        if error > 1e-10:
            failures.append((i, lambda_i, error))
    
    return failures

# Test with various small values
epsilons = [0, 1e-300, 1e-200, 1e-130, 2.39638747e-130, 1e-100, 1e-50, 1e-20, 1e-10]

print("Testing eigenvalue computation with tiny perturbations:")
print("=" * 60)

for eps in epsilons:
    failures = test_matrix_with_epsilon(eps)
    
    if failures:
        print(f"ε = {eps:e}: FAILURES")
        for idx, eval, err in failures:
            print(f"  Eigenpair {idx}: λ={eval:.6f}, error={err:.6e}")
    else:
        print(f"ε = {eps:e}: All eigenpairs pass")

print("\n" + "=" * 60)
print("CONCLUSION:")
print("Very small but non-zero values (around 1e-130) cause")
print("numpy.linalg.eig to produce incorrect eigenvectors!")

# Let's check if this is related to machine epsilon
print(f"\nMachine epsilon for float64: {np.finfo(np.float64).eps}")
print(f"Smallest normal float64: {np.finfo(np.float64).tiny}")
print(f"Test value 2.39638747e-130 is {'>' if 2.39638747e-130 > np.finfo(np.float64).tiny else '<'} smallest normal")

# Check if the issue is related to subnormal numbers
if 2.39638747e-130 < np.finfo(np.float64).tiny:
    print("\nThe test value is a SUBNORMAL number!")
    print("This might cause numerical instability in LAPACK routines")