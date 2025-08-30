# Intended to be run once new packages are in the repo but not-commited post-autobuild

'''
Precondition: Current directory is the repository directory
'''

import os
import subprocess
from typing import Any
from .RepoManager import RepoManager

def main():
    repo = RepoManager(os.getcwd())
    packages :  dict[str, dict[str, Any]] = repo.get_current_state()
    packages_with_updates : list[str] = repo.get_updates()
    for package in packages_with_updates:
        current_version : str = ""
        if package in packages:
            print(f"Updating {package}")
            current_version = packages[package]["version"]
        version : str = repo.extract_and_process_version(package, current_version)
        subprocess.run(f'git add {package}.tar.xz && git commit -m "Update {package} to {version}"', shell=True, cwd="packages")
    

