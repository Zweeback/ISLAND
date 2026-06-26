import time
import os
from pathlib import Path
import sys

# Create a mock environment
os.makedirs("bench_dir", exist_ok=True)

def original_scan():
    file_entries = []
    root_path = Path("bench_dir")
    for root, dirs, files in os.walk(root_path):
        for file in files:
            file_path = Path(root) / file
            try:
                stat = file_path.stat()
                file_entries.append({
                    "name": file,
                    "path": file_path.as_posix(),
                    "size_bytes": stat.st_size,
                    "modified": stat.st_mtime
                })
            except Exception:
                pass
    return file_entries

def walk_string_scan():
    file_entries = []
    root_path = "bench_dir"
    for root, dirs, files in os.walk(root_path):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                stat = os.stat(file_path)
                file_entries.append({
                    "name": file,
                    "path": file_path.replace("\\", "/"),
                    "size_bytes": stat.st_size,
                    "modified": stat.st_mtime
                })
            except Exception:
                pass
    return file_entries

def scandir_scan():
    file_entries = []
    root_path = "bench_dir"

    def _scan(directory):
        try:
            with os.scandir(directory) as it:
                for entry in it:
                    if entry.is_dir(follow_symlinks=False):
                        _scan(entry.path)
                    elif entry.is_file(follow_symlinks=False):
                        try:
                            stat = entry.stat()
                            file_entries.append({
                                "name": entry.name,
                                "path": entry.path.replace("\\", "/"),
                                "size_bytes": stat.st_size,
                                "modified": stat.st_mtime
                            })
                        except Exception:
                            pass
        except Exception:
            pass

    _scan(root_path)
    return file_entries

start = time.time()
original_scan()
print("Original:", time.time() - start)

start = time.time()
walk_string_scan()
print("os.walk + string:", time.time() - start)

start = time.time()
scandir_scan()
print("os.scandir:", time.time() - start)
