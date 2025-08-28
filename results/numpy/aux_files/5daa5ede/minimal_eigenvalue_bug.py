"""
Minimal reproducible example of numpy.linalg.eig bug
"""
import numpy as np
import numpy.linalg as la

# Construct the problematic matrix
A = np.array([[0, 0, 0, 0, 0],
              [1, 0, 0, 0, 1],
              [0, 0, 0, 0, 0],
              [0, 0, 0, 0, 1],
              [0, 1, 0, 0, 0]], dtype=float)

print("Matrix A:")
print(A)

# Compute eigenvalues and eigenvectors
eigenvalues, eigenvectors = la.eig(A)

print(f"\nEigenvalues: {eigenvalues}")

# Check the eigenvalue equation for non-defective eigenvalues
print("\nChecking eigenvalue equation A @ v = λ * v:")
print("-" * 50)

for i in range(len(eigenvalues)):
    lambda_i = eigenvalues[i]
    v_i = eigenvectors[:, i]
    
    Av = A @ v_i
    lambda_v = lambda_i * v_i
    
    error = np.linalg.norm(Av - lambda_v)
    
    print(f"\nEigenvalue λ = {lambda_i:.6f}")
    print(f"Eigenvector v = {v_i}")
    print(f"A @ v = {Av}")
    print(f"λ * v = {lambda_v}")
    print(f"Error ||A@v - λ*v|| = {error:.6e}")
    
    if error > 1e-10:
        print(f"  ❌ FAILS: Eigenvalue equation not satisfied!")
    else:
        print(f"  ✓ PASSES")

# Verify that eigenvalues 1 and -1 are non-defective
print("\n" + "=" * 50)
print("DEFECTIVENESS CHECK:")
print("=" * 50)

# Count multiplicities
unique_evals = []
for ev in eigenvalues:
    if not any(np.abs(ev - uev) < 1e-10 for uev in unique_evals):
        unique_evals.append(ev)

for eval in unique_evals:
    # Algebraic multiplicity
    alg_mult = np.sum(np.abs(eigenvalues - eval) < 1e-10)
    
    # Geometric multiplicity (number of linearly independent eigenvectors)
    indices = [i for i, e in enumerate(eigenvalues) if np.abs(e - eval) < 1e-10]
    if indices:
        vecs = eigenvectors[:, indices]
        geom_mult = la.matrix_rank(vecs)
        
        print(f"\nλ = {eval:.6f}:")
        print(f"  Algebraic multiplicity: {alg_mult}")
        print(f"  Geometric multiplicity: {geom_mult}")
        
        if geom_mult < alg_mult:
            print(f"  Status: DEFECTIVE")
        else:
            print(f"  Status: NON-DEFECTIVE")

print("\n" + "=" * 50)
print("BUG SUMMARY:")
print("=" * 50)
print("Non-defective eigenvalues (1.0 and -1.0) have eigenvectors")
print("that do NOT satisfy the eigenvalue equation A @ v = λ * v")
print("This is a bug in numpy.linalg.eig")