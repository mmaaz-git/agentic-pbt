import numpy as np
import numpy.linalg as la

# The exact failing matrix from the original test
A = np.array([[0.00000000e+000, 0.00000000e+000, 0.00000000e+000,
               2.39638747e-130, 0.00000000e+000],
              [1.00000000e+000, 0.00000000e+000, 0.00000000e+000,
               0.00000000e+000, 1.00000000e+000],
              [0.00000000e+000, 0.00000000e+000, 0.00000000e+000,
               0.00000000e+000, 0.00000000e+000],
              [0.00000000e+000, 0.00000000e+000, 0.00000000e+000,
               0.00000000e+000, 1.00000000e+000],
              [0.00000000e+000, 1.00000000e+000, 0.00000000e+000,
               0.00000000e+000, 0.00000000e+000]])

print("Matrix A:")
print(A)
print(f"\nMatrix properties:")
print(f"Shape: {A.shape}")
print(f"Rank: {la.matrix_rank(A)}")
print(f"Determinant: {la.det(A)}")
print(f"Norm: {la.norm(A)}")

# Get eigenvalues and eigenvectors
eigenvalues, eigenvectors = la.eig(A)

print(f"\nEigenvalues: {eigenvalues}")

# Let's check which eigenpairs actually fail
failing_pairs = []
for i in range(len(eigenvalues)):
    lambda_i = eigenvalues[i]
    v_i = eigenvectors[:, i]
    
    Av = A @ v_i
    lambda_v = lambda_i * v_i
    
    error = np.linalg.norm(Av - lambda_v)
    rel_error = error / (np.linalg.norm(v_i) + 1e-10)
    
    if error > 1e-10:
        failing_pairs.append({
            'index': i,
            'eigenvalue': lambda_i,
            'eigenvector': v_i,
            'Av': Av,
            'lambda_v': lambda_v,
            'error': error,
            'rel_error': rel_error
        })

print(f"\nNumber of failing eigenpairs: {len(failing_pairs)} out of {len(eigenvalues)}")

if failing_pairs:
    print("\n=== DETAILED ANALYSIS OF FAILURES ===")
    for fp in failing_pairs:
        print(f"\nEigenpair {fp['index']}:")
        print(f"  Eigenvalue: {fp['eigenvalue']}")
        print(f"  Eigenvector: {fp['eigenvector']}")
        print(f"  A @ v = {fp['Av']}")
        print(f"  λ * v = {fp['lambda_v']}")
        print(f"  Error: {fp['error']}")
        print(f"  Relative error: {fp['rel_error']}")

# Let's check if this is a defective matrix
print("\n=== DEFECTIVENESS CHECK ===")

# For each eigenvalue, count geometric vs algebraic multiplicity
from collections import Counter
eigenvalue_counts = Counter(np.round(eigenvalues, 10))

print("Eigenvalue multiplicities:")
for eval, count in eigenvalue_counts.items():
    print(f"  λ = {eval}: algebraic multiplicity = {count}")
    
    # Find geometric multiplicity (dimension of eigenspace)
    # This is the number of linearly independent eigenvectors for this eigenvalue
    indices = [i for i, e in enumerate(eigenvalues) if np.abs(e - eval) < 1e-10]
    if indices:
        vecs = eigenvectors[:, indices]
        # Check linear independence using rank
        geom_mult = la.matrix_rank(vecs)
        print(f"            geometric multiplicity = {geom_mult}")
        
        if geom_mult < count:
            print(f"    -> DEFECTIVE (geometric < algebraic)")

# Let's try to understand the structure better
print("\n=== MATRIX STRUCTURE ===")

# Check if it's block triangular
print("Upper left 2x2 block:")
print(A[:2, :2])
print("Upper right 2x3 block:")
print(A[:2, 2:])
print("Lower left 3x2 block:")
print(A[2:, :2])
print("Lower right 3x3 block:")
print(A[2:, 2:])

# The issue might be that numpy.linalg.eig doesn't handle defective matrices well
# Let's check with scipy if available
try:
    import scipy.linalg
    print("\n=== SCIPY COMPARISON ===")
    scipy_eigenvalues, scipy_eigenvectors = scipy.linalg.eig(A)
    print(f"Scipy eigenvalues: {scipy_eigenvalues}")
    
    # Check scipy eigenpairs
    scipy_failures = 0
    for i in range(len(scipy_eigenvalues)):
        v = scipy_eigenvectors[:, i]
        l = scipy_eigenvalues[i]
        error = np.linalg.norm(A @ v - l * v)
        if error > 1e-10:
            scipy_failures += 1
            print(f"Scipy eigenpair {i} error: {error}")
    
    print(f"Scipy failing pairs: {scipy_failures}")
    
except ImportError:
    print("\nScipy not available for comparison")

# Final check: Is this genuinely a bug or expected behavior?
print("\n=== BUG ASSESSMENT ===")

if len(failing_pairs) > 0:
    # Check if the failures are for defective eigenvalues
    defective_eigenvalues = []
    for eval, count in eigenvalue_counts.items():
        indices = [i for i, e in enumerate(eigenvalues) if np.abs(e - eval) < 1e-10]
        if indices:
            vecs = eigenvectors[:, indices]
            geom_mult = la.matrix_rank(vecs)
            if geom_mult < count:
                defective_eigenvalues.append(eval)
    
    failing_eigenvalues = [fp['eigenvalue'] for fp in failing_pairs]
    
    print(f"Defective eigenvalues: {defective_eigenvalues}")
    print(f"Failing eigenvalues: {failing_eigenvalues}")
    
    # Check if failures are only for defective eigenvalues
    all_failures_defective = all(
        any(np.abs(fe - de) < 1e-10 for de in defective_eigenvalues)
        for fe in failing_eigenvalues
    )
    
    if all_failures_defective:
        print("All failures are for defective eigenvalues - this might be expected behavior")
        print("NumPy's eig might not guarantee valid eigenvectors for defective matrices")
    else:
        print("*** POTENTIAL BUG: Non-defective eigenvalues are failing! ***")
        print("This suggests a genuine issue in numpy.linalg.eig")
        
        # Find which non-defective eigenvalues fail
        for fp in failing_pairs:
            is_defective = any(np.abs(fp['eigenvalue'] - de) < 1e-10 for de in defective_eigenvalues)
            if not is_defective:
                print(f"  Non-defective eigenvalue {fp['eigenvalue']} fails with error {fp['error']}")