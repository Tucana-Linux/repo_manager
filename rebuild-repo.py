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
        depends_str : str | None = None
        
        with tarfile.open(f"packages/{package}.tar.xz", "r:xz") as tar:
            for member in tar.getmembers():
                if os.path.basename(member.name) == "depends":
                    f = tar.extractfile(member)
                    if f:
                        depends_str = f.read().decode().strip()
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
        extracted_version : str | None = None
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
    
    def generate_file_list(self, package: str) -> list[str]:
        """
        Returns a list of all file paths in the tarball for the given package.
        """

        file_list : list[str] = []
        with tarfile.open(f"packages/{package}.tar.xz", 'r:xz') as tar:
            for member in tar.getmembers():
                if member.isfile():
                    file_list.append(member.name)
        return file_list

    def write_file_list(self, package: str) -> None:
        """
        Writes the list of file paths from the tarball to file-lists/<package>.
        """
        file_list = self.generate_file_list(package)
        os.makedirs("file-lists", exist_ok=True)
        with open(f"file-lists/{package}", "w") as f:
            for file_path in file_list:
                f.write(f"{file_path}\n")

    
    def write_repo(self, packages : dict[str, dict[str, Any]]):
        with open("available-packages/packages.yaml", "w") as packages_yaml:
            yaml.safe_dump(packages, packages_yaml)
        with open('time', 'w') as f:
            f.write(str(int(time.time())))

def find_missing_depends(package: dict[str, Any], param : str, current_state : dict[str, dict[str, Any]]) -> set[str]:
    missing_dependencies : set[str] = set()
    for depend in package[param]:
        if depend not in current_state.keys():
            missing_dependencies.add(depend)
    return missing_dependencies

def validate_state(state: dict[str, dict[str, Any]]) -> bool:
    for package_name, package in state.items():
        missing_dependencies : set[str] =  find_missing_depends(package, "depends", state)
        missing_make_dependencies : set[str] =  find_missing_depends(package, "make_depends",  state)
        if missing_dependencies or missing_make_dependencies:
            print(f"ERROR Repo State validation failed, {package_name} requires {list(missing_dependencies)} {list(missing_make_dependencies)} which could not be found")
            return False
    return True

repo = RepoManager(os.getcwd())
packages :  dict[str, dict[str, Any]] = repo.get_current_state()
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
    repo.write_file_list(package)

print("Validating Repo State...")
if validate_state(packages):
    print("Writing Repo...")
    repo.write_repo(packages)

 
    

    



