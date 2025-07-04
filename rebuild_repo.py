import os
from typing import Any
from .RepoManager import RepoManager


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
def main() -> None:
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

 
main()