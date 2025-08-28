import numpy as np
import scipy.cluster.hierarchy as hier
from scipy.spatial.distance import pdist

# Minimal failing case from Hypothesis
obs = np.array([[0., 0.],
                [0., 0.],
                [0., 0.],
                [0., 0.]])

print("Input observations:")
print(obs)
print()

# Create linkage
Z = hier.linkage(obs, method='average')
print("Linkage matrix Z:")
print(Z)
print()

# Compute pairwise distances
Y = pdist(obs)
print("Pairwise distances Y:")
print(Y)
print()

# Compute cophenetic correlation
c, coph_dists = hier.cophenet(Z, Y)
print("Cophenetic correlation coefficient:", c)
print("Is NaN?", np.isnan(c))
print()

# The issue is that when all observations are identical:
# - All pairwise distances are 0
# - This leads to division by zero in correlation calculation
# - Should return a defined value (likely 1.0) or raise an informative error

# Test with slightly different data
obs2 = np.array([[0., 0.],
                 [0., 0.],
                 [0., 0.],
                 [1., 1.]])

Z2 = hier.linkage(obs2, method='average')
Y2 = pdist(obs2)
c2, _ = hier.cophenet(Z2, Y2)
print("With non-identical points, correlation:", c2)