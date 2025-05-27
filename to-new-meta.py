""" 
Converts the oldmeta data scheme to the new one
"""
import os
import yaml
import tarfile
from typing import Any

def get_uncompressed_size(file_path: str) -> int:
    total_uncompressed_size = 0
    with tarfile.open(file_path, 'r:xz') as tar:
        for member in tar.getmembers():
            total_uncompressed_size += member.size
    return int(total_uncompressed_size) // 1024

packages : dict[str, dict[str, Any]] = {}
with open("available-packages/versions", "r") as file:
    versions = dict(
    line.strip().split(": ") for line in file if line.strip())
    
for pkg, version in versions.items():
    packages[pkg] = {}
    last_update : int = int(os.path.getmtime(f"packages/{pkg}.tar.xz"))
    download_size : int = os.path.getsize(f"packages/{pkg}.tar.xz") // 1024
    install_size : int = get_uncompressed_size(f"packages/{pkg}.tar.xz")
    with open(f"depend/depend-{pkg}", "r") as file:
        depends_string : str = file.readline().strip()
        depends_list : list[str] = depends_string.split() if depends_string else []
        
    packages[pkg] = {
        "version": version,
        "depends": depends_list,
        "download_size": download_size,
        "install_size": install_size,
        "last_update": last_update
    }
    
with open("packages.yaml", "w") as file:
    yaml.safe_dump(packages, file)
    
    
 