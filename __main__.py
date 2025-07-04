from .commit_packages import main as commit
from .rebuild_repo import main as rebuild
import sys


def main() -> None:
    if "commit" in sys.argv:
        commit()
        return
    if "rebuild-meta" in sys.argv:
        rebuild()
        return
    else:
        print("Usage: rebuild-meta -- Rebuild the metafiles\ncommit -- commit packages directory does not push")
        
if __name__ == "__main__":
    main()
