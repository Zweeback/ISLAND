from __future__ import annotations
import os
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import TypedDict

class FileEntry(TypedDict):
    name: str
    path: str
    size_bytes: int
    modified: str

class ScanReport(TypedDict):
    catalog_type: str
    timestamp: str
    scan_roots: list[str]
    data: dict[str, list[FileEntry]]

# Default folders to index
DEFAULT_PATHS: list[Path] = [
    Path("C:/Users/derzw/Desktop"),
    Path("C:/Users/derzw/Downloads"),
    Path("G:/Meine Ablage")
]

# Strict folder exclusion names
EXCLUDED_DIR_NAMES: set[str] = {
    "node_modules", "venv", ".venv", ".git", ".ssh", "AppData",
    "Program Files", "Program Files (x86)", "Windows", "System32",
    ".gemini", ".continue"
}

# Strict file exclusion prefixes/suffixes
EXCLUDED_FILE_PATTERNS: list[str] = [
    ".env", "passwords", "id_rsa", "secret"
]

class LocalIndexer:
    paths: list[Path]

    def __init__(self, paths: list[Path]) -> None:
        self.paths = paths

    def should_exclude_dir(self, dir_name: str) -> bool:
        return dir_name in EXCLUDED_DIR_NAMES

    def should_exclude_file(self, file_name: str) -> bool:
        lower_name = file_name.lower()
        for pattern in EXCLUDED_FILE_PATTERNS:
            if pattern in lower_name:
                return True
        return False

    def scan(self) -> ScanReport:
        catalog: dict[str, list[FileEntry]] = {}
        
        for root_path in self.paths:
            if not root_path.exists():
                print(f"Path does not exist: {root_path}", file=sys.stderr)
                continue
                
            print(f"Scanning directory: {root_path}", file=sys.stderr)
            file_entries: list[FileEntry] = []
            
            for root, dirs, files in os.walk(root_path):
                # Modify dirs in-place to skip excluded directories during walk
                dirs[:] = [d for d in dirs if not self.should_exclude_dir(d)]
                
                for file in files:
                    if self.should_exclude_file(file):
                        continue
                        
                    file_path = Path(root) / file
                    try:
                        stat = file_path.stat()
                        file_entries.append({
                            "name": file,
                            "path": file_path.as_posix(),
                            "size_bytes": stat.st_size,
                            "modified": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()
                        })
                    except Exception as e:
                        # Skip files that we can't access
                        print(f"Skipping inaccessible file {file}: {e}", file=sys.stderr)
                        continue
                        
            catalog[root_path.as_posix()] = file_entries
            
        return {
            "catalog_type": "local_pc_inventory",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "scan_roots": [p.as_posix() for p in self.paths],
            "data": catalog
        }

def main() -> None:
    # Use default paths or optional args
    paths_to_scan = DEFAULT_PATHS
    if len(sys.argv) > 1:
        paths_to_scan = [Path(p) for p in sys.argv[1:]]
        
    indexer = LocalIndexer(paths_to_scan)
    report = indexer.scan()
    
    # Save the index to .tmp folder inside blast_agent directory
    tmp_dir = Path("c:/Users/derzw/Desktop/00_ZENTRALE_INSEL/08_TOOLS_SCRIPTS/blast_agent/.tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    
    out_file = tmp_dir / "local_inventory_index.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully compiled local inventory scan to {out_file.as_posix()}", file=sys.stderr)
    # Print high level stats to stdout
    summary = {
        "roots_scanned": len(report["scan_roots"]),
        "total_files_indexed": sum(len(files) for files in report["data"].values()),
        "output_path": out_file.as_posix()
    }
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
