import os
import yaml
from typing import Any
import tarfile
import time

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
                if ".git" in tar:
                    continue
                if os.path.getmtime(f"./{tar}") > last_repo_update:
                    needs_update.append(tar.removesuffix(".tar.xz"))
        os.chdir(self.repo_path)
        return needs_update
    
    def extract_depends(self, package: str) -> list[str]:
        
        depends_str : str = ""
        with tarfile.open(f"packages/{package}.tar.xz", "r:xz") as tar:
            for member in tar.getmembers():
                if os.path.basename(member.name) == "depends":
                    f = tar.extractfile(member)
                    if f:
                        depends_str = f.read().decode().strip()
                        return depends_str.split()
                    
        if not depends_str:
            raise ValueError("No 'depends' file found in the archive.")

    def extract_make_depends(self, package: str) -> list[str]:
        depends_str : str = ""
        
        with tarfile.open(f"packages/{package}.tar.xz", "r:xz") as tar:
            for member in tar.getmembers():
                if os.path.basename(member.name) == "make-depends":
                    f = tar.extractfile(member)
                    if f:
                        depends_str : str = f.read().decode().strip()
                        return depends_str.split()
        return []

        
        
    def extract_and_process_version(self, package: str, current_version: str) -> str:
        extracted_version : str | None = None
        # Extract version file
        with tarfile.open(f"packages/{package}.tar.xz", "r:xz") as tar:
            for member in tar.getmembers():
                if member.name == f"{package}/version":
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
