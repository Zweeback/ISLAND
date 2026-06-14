import sys
import subprocess
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).parent.resolve()

def init_workspace() -> None:
    """
    Checks the directory and ensures all required directories and files are present.
    """
    print(f"Initializing/Verifying B.L.A.S.T. Workspace at {WORKSPACE_ROOT.as_posix()}...", file=sys.stderr)
    
    # Required directories
    dirs = [
        WORKSPACE_ROOT / ".context",
        WORKSPACE_ROOT / "architecture",
        WORKSPACE_ROOT / "tools",
        WORKSPACE_ROOT / ".tmp"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"Verified directory: {d.relative_to(WORKSPACE_ROOT)}", file=sys.stderr)

    # Required files list
    files = [
        WORKSPACE_ROOT / "gemini.md",
        WORKSPACE_ROOT / ".env.template",
        WORKSPACE_ROOT / ".env",
        WORKSPACE_ROOT / ".context/active_brief.md",
        WORKSPACE_ROOT / ".context/system_map.json",
        WORKSPACE_ROOT / "architecture/sop_agent_run.md",
        WORKSPACE_ROOT / "architecture/sop_scrapers.md",
        WORKSPACE_ROOT / "tools/__init__.py",
        WORKSPACE_ROOT / "tools/scraper_opendata_dortmund.py",
        WORKSPACE_ROOT / "tools/scraper_digibib.py",
        WORKSPACE_ROOT / "tools/scraper_scribd.py",
        WORKSPACE_ROOT / "tools/scraper_statista.py",
        WORKSPACE_ROOT / "tools/scraper_linkedin.py",
        WORKSPACE_ROOT / "tools/inventory_compiler.py",
        WORKSPACE_ROOT / "tools/agent_loop.py"
    ]
    
    all_ok = True
    for f in files:
        if f.exists():
            print(f"Verified file: {f.relative_to(WORKSPACE_ROOT)}", file=sys.stderr)
        else:
            print(f"WARNING: Missing file: {f.relative_to(WORKSPACE_ROOT)}", file=sys.stderr)
            all_ok = False
            
    if all_ok:
        print("\nAll workspace files verified successfully!", file=sys.stderr)
    else:
        print("\nSome files were missing. Run setup scripts to regenerate them.", file=sys.stderr)

def run_agent() -> None:
    """
    Runs the agent reasoning loop.
    """
    loop_script = WORKSPACE_ROOT / "tools" / "agent_loop.py"
    if not loop_script.exists():
        print(f"Error: Agent loop script not found at {loop_script.as_posix()}", file=sys.stderr)
        sys.exit(1)
        
    print("Running B.L.A.S.T. Agent Loop...", file=sys.stderr)
    res = subprocess.run([sys.executable, str(loop_script)], capture_output=False)
    sys.exit(res.returncode)

def run_scraper(scraper_name: str, args: list[str]) -> None:
    """
    Directly runs a scraper module from CLI.
    """
    if scraper_name == "opendata":
        scraper_name = "opendata_dortmund"
    scraper_file = WORKSPACE_ROOT / "tools" / f"scraper_{scraper_name}.py"
    if not scraper_file.exists():
        print(f"Error: Scraper scraper_{scraper_name}.py not found.", file=sys.stderr)
        sys.exit(1)
        
    cmd = [sys.executable, str(scraper_file)] + args
    res = subprocess.run(cmd)
    sys.exit(res.returncode)

def run_inventory(args: list[str]) -> None:
    """
    Directly runs the local directory indexer.
    """
    indexer_file = WORKSPACE_ROOT / "tools" / "inventory_compiler.py"
    if not indexer_file.exists():
        print("Error: inventory_compiler.py not found.", file=sys.stderr)
        sys.exit(1)
        
    cmd = [sys.executable, str(indexer_file)] + args
    res = subprocess.run(cmd)
    sys.exit(res.returncode)

def main() -> None:
    if len(sys.argv) < 2:
        print("B.L.A.S.T. Local Agentic System CLI")
        print("Commands:")
        print("  init                      Verify and initialize workspace structure")
        print("  run                       Run the autonomous agent loop")
        print("  scrape <name> <cmd> <arg> Directly run a scraper (opendata|digibib|scribd|statista|linkedin)")
        print("  inventory                 Directly compile local PC directory scan")
        sys.exit(1)
        
    cmd = sys.argv[1]
    
    if cmd == "init":
        init_workspace()
    elif cmd == "run":
        run_agent()
    elif cmd == "scrape":
        if len(sys.argv) < 3:
            print("Usage: python blast_agent.py scrape <opendata|digibib|scribd|statista|linkedin> <scraper_args...>")
            sys.exit(1)
        run_scraper(sys.argv[2], sys.argv[3:])
    elif cmd == "inventory":
        run_inventory(sys.argv[2:])
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)

if __name__ == "__main__":
    main()
