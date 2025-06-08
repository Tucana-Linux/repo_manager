import os
from typing import Any
import yaml
import time
import tarfile

class RepoManager:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        os.chdir(repo_path)
            
    def get_current_state(self) -> dict[str, dict[str, Any]]:
        with open("available-packages/packages.yaml", "r") as packages_yaml:
            return yaml.safe_load(packages_yaml)
            
    def get_updates(self) -> list[str]:
        needs_update : list[str] = []
        with open("./time", "r") as f:
            last_repo_update = float(f.readline().strip())
        os.chdir("packages/")
        for _, _, files in os.walk("."):
            for tar in files:
                if os.path.getmtime(f"./{tar}") > last_repo_update:
                    needs_update.append(tar.removesuffix(".tar.xz"))
        os.chdir(self.repo_path)
        return needs_update
    
    def extract_depends(self, package: str) -> list[str]:
        depends_str : str = None
        
        with tarfile.open(f"packages/{package}.tar.xz", "r:xz") as tar:
            for member in tar.getmembers():
                if os.path.basename(member.name) == "depends":
                    f = tar.extractfile(member)
                    if f:
                        depends_str : str = f.read().decode().strip()
                        break

        if depends_str is None:
            raise ValueError("No 'depends' file found in the archive.")
        
        return depends_str.split()

    def extract_make_depends(self, package: str) -> list[str]:
        depends_str : str = ""
        
        with tarfile.open(f"packages/{package}.tar.xz", "r:xz") as tar:
            for member in tar.getmembers():
                if os.path.basename(member.name) == "make-depends":
                    f = tar.extractfile(member)
                    if f:
                        depends_str : str = f.read().decode().strip()
                        break

        return depends_str.split()
        
        
    def extract_and_process_version(self, package: str, current_version: str) -> str:
        extracted_version : str = None
        # Extract version file
        with tarfile.open(f"packages/{package}.tar.xz", "r:xz") as tar:
            for member in tar.getmembers():
                if os.path.basename(member.name) == "version":
                    f = tar.extractfile(member)
                    if f:
                        extracted_version = f.read().decode().strip()
                        break

        if not extracted_version:
            raise ValueError("No 'version' file found in the archive.")
        
        rev : int = 0
        
        if "-" in current_version:
            base_version, old_rev = current_version.rsplit("-", 1)
            if base_version == extracted_version and old_rev.isdigit():
                rev = int(old_rev) + 1 
            
        return f"{extracted_version}-{rev}"
        
    def get_download_size(self, package: str) -> int:
        return os.path.getsize(f"packages/{package}.tar.xz") // 1024
    
    def get_install_size(self, package: str) -> int:
        total_uncompressed_size = 0
        with tarfile.open(f"packages/{package}.tar.xz", 'r:xz') as tar:
            for member in tar.getmembers():
                total_uncompressed_size += member.size
        return int(total_uncompressed_size) // 1024
    
    def get_last_update(self, package: str) -> int:
        return int(os.path.getmtime(f"{self.repo_path}/packages/{package}.tar.xz"))
    
    def write_repo(self, packages : dict[str, dict[str, Any]]):
        with open("available-packages/packages.yaml", "w") as packages_yaml:
            yaml.safe_dump(packages, packages_yaml)
        with open('time', 'w') as f:
            f.write(str(int(time.time())))
            
    
    
    
repo = RepoManager(os.getcwd())
packages :  dict[str, dict[str, Any]] = repo.get_current_state()
print("Getting Updates")
packages_with_updates : list[str] = repo.get_updates()
print(f"Packages with updates {packages_with_updates}")

for package in packages_with_updates:
    print(f"Working on {package}")
    package_dict = {}
    current_version : str = ""
    if package in packages:
        current_version = packages[package]["version"]
    package_dict["version"] = repo.extract_and_process_version(package, current_version)
    package_dict["depends"] = repo.extract_depends(package)
    package_dict["make_depends"] = repo.extract_make_depends(package)
    package_dict["install_size"] = repo.get_install_size(package)
    package_dict["download_size"] = repo.get_download_size(package)
    package_dict["last_update"] = repo.get_last_update(package)
    
    packages[package] = package_dict

repo.write_repo(packages)

 
    

    



