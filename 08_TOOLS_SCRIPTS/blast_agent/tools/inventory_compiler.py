import os
import json
import sys
import fnmatch
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

# Dynamischer Default: Projekt-Root anstelle von lokalen Windows-Ordnern!
DEFAULT_WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Strikte Ausschluss-Verzeichnisse
EXCLUDED_DIR_NAMES: set[str] = {
    "node_modules", "venv", ".venv", ".git", ".ssh", "AppData",
    "Program Files", "Program Files (x86)", "Windows", "System32",
    ".gemini", ".continue", ".tmp"
}

# Strikte Ausschluss-Muster (Sicherheitsrelevante Filter)
EXCLUDED_FILE_PATTERNS: list[str] = [
    ".env", "passwords", "id_rsa", "secret", "cookie", "token", "key"
]

class LocalIndexer:
    paths: list[Path]
    ignore_patterns: list[str]

    def __init__(self, paths: list[Path], workspace_root: Path) -> None:
        self.paths = paths
        self.workspace_root = workspace_root
        self.ignore_patterns = self._load_gitignore_patterns()

    def _load_gitignore_patterns(self) -> list[str]:
        """
        Liest die lokale .gitignore ein, um private Dateien zu schuetzen.
        """
        patterns = []
        gitignore_path = self.workspace_root / ".gitignore"
        if gitignore_path.exists():
            try:
                with open(gitignore_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            patterns.append(line)
            except Exception as e:
                print(f"Warnung: .gitignore konnte nicht gelesen werden: {e}", file=sys.stderr)
        return patterns

    def should_exclude_dir(self, dir_name: str) -> bool:
        if dir_name in EXCLUDED_DIR_NAMES:
            return True
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(dir_name, pattern.rstrip("/")):
                return True
        return False

    def should_exclude_file(self, file_name: str) -> bool:
        lower_name = file_name.lower()
        for pattern in EXCLUDED_FILE_PATTERNS:
            if pattern in lower_name:
                return True
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(file_name, pattern):
                return True
        return False

    def scan(self) -> ScanReport:
        catalog: dict[str, list[FileEntry]] = {}
        
        for root_path in self.paths:
            if not root_path.exists():
                print(f"Pfad existiert nicht: {root_path}", file=sys.stderr)
                continue
                
            print(f"Scanne Verzeichnis: {root_path}", file=sys.stderr)
            file_entries: list[FileEntry] = []
            
            for root, dirs, files in os.walk(root_path):
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
                        print(f"Uberspringe Datei {file}: {e}", file=sys.stderr)
                        continue
                        
            catalog[root_path.as_posix()] = file_entries
            
        return {
            "catalog_type": "local_pc_inventory",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "scan_roots": [p.as_posix() for p in self.paths],
            "data": catalog
        }

def main() -> None:
    # REIHENFOLGE: 1. CLI-Argumente, 2. Env-Variable, 3. Workspace Root (Fallback)
    env_scan_path = os.getenv("BLAST_SCAN_PATH")

    if len(sys.argv) > 1:
        paths_to_scan = [Path(p) for p in sys.argv[1:]]
    elif env_scan_path:
        paths_to_scan = [Path(env_scan_path)]
    else:
        paths_to_scan = [DEFAULT_WORKSPACE_ROOT]
        
    indexer = LocalIndexer(paths_to_scan, DEFAULT_WORKSPACE_ROOT)
    report = indexer.scan()
    
    tmp_dir = Path(__file__).resolve().parent.parent / ".tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    
    out_file = tmp_dir / "local_inventory_index.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        
    print(f"Erfolgreich Inventar-Scan kompiliert nach: {out_file.as_posix()}", file=sys.stderr)

    summary = {
        "roots_scanned": len(report["scan_roots"]),
        "total_files_indexed": sum(len(files) for files in report["data"].values()),
        "output_path": out_file.as_posix()
    }
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
