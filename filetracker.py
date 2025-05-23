# === File: filetracker.py ===
import os
import hashlib
from pathlib import Path
import json
from datetime import datetime
from config import WKSPACE, EXCLUDE_DIRS



class FileChangeTracker:
    def __init__(self, WKSPACE):
        self.WKSPACE = Path(WKSPACE).expanduser().resolve()
        self.snapshot_file = self.WKSPACE / ".file_snapshot.json"

    def _hash_file(self, path):
        try:
            with open(path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return None

    def snapshot(self):
        snapshot = {}

        for root, dirs, files in os.walk(self.WKSPACE):
            # Exclude directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

            for fname in files:
                if fname.endswith(".py"):
                    fpath = Path(root) / fname
                    rel_path = str(fpath.relative_to(self.WKSPACE))
                    snapshot[rel_path] = self._hash_file(fpath)
        with open(self.snapshot_file, "w") as f:
            json.dump(snapshot, f, indent=2)
        print(f"Snapshot saved with {len(snapshot)} Python files.")

    def diff(self, verbose=False):
        if not self.snapshot_file.exists():
            print("No snapshot found. Run snapshot() first.")
            return []

        with open(self.snapshot_file) as f:
            old_snapshot = json.load(f)

        current_snapshot = {}
        changes = []


        for root, dirs, files in os.walk(self.WKSPACE):
            # Exclude directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

            for fname in files:
                if fname.endswith(".py"):
                    fpath = Path(root) / fname
                    rel_path = str(fpath.relative_to(self.WKSPACE))
                    file_hash = self._hash_file(fpath)
                    current_snapshot[rel_path] = file_hash

                    if rel_path not in old_snapshot:
                        changes.append(("ADDED", rel_path))
                    elif old_snapshot[rel_path] != file_hash:
                        changes.append(("MODIFIED", rel_path))

        for rel_path in old_snapshot:
            if rel_path not in current_snapshot:
                changes.append(("DELETED", rel_path))

        if verbose:
            for change_type, path in changes:
                print(f"{change_type}: {path}")
        else:
            print(f"{len(changes)} file(s) changed.")

        return changes


if __name__ == "__main__":
    tracker = FileChangeTracker(WKSPACE)
    tracker.snapshot()  # Run once to save a snapshot
    print("Changes since last snapshot:")
    tracker.diff(verbose=True)
