#!/usr/bin/env python3
import pkg_resources

# List all installed packages
installed_packages = [d.project_name for d in pkg_resources.working_set]
installed_packages.sort()

print("Installed packages:")
for package in installed_packages:
    if 'copier' in package.lower():
        print(f"  - {package}")

# Try to find copier package
try:
    copier_dist = pkg_resources.get_distribution('copier')
    print(f"\nCopier found at: {copier_dist.location}")
except pkg_resources.DistributionNotFound:
    print("\nCopier not found in installed packages")