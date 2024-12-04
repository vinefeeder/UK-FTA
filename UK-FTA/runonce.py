## install modules from requirements.txt

import subprocess
import sys
import os
import pkg_resources

def install_packages_from_requirements(requirements_file):
    requirements_path = os.path.join(os.getcwd(), requirements_file)
    installed_packages = {pkg.key for pkg in pkg_resources.working_set}
    packages_to_install = []

    with open(requirements_path, 'r') as f:
        for line in f:
            package = line.strip()
            if package and package not in installed_packages:
                packages_to_install.append(package)

    if packages_to_install:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_path])
            print(f"Packages from {requirements_file} have been installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error installing packages from {requirements_file}: {e}")
    else:
        print(f"All packages from {requirements_file} are already installed.")
        
        
if __name__ == '__main__':
    install_packages_from_requirements('requirements.txt')