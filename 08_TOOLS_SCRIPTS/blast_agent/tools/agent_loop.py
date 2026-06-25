import os
import sys
import json
import re
import urllib.request
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

def load_env(env_path: Path) -> dict[str, str]:
    env = {}
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        env[parts[0].strip()] = parts[1].strip()
    return env

def call_llm(api_key: str, system_prompt: str, user_prompt: str, model_name: str = "gpt-4o-mini") -> str:
    """
    Direkter HTTP-Request an die OpenAI Schnittstelle.
    Ermöglicht dynamische Modellkonfiguration über die .env-Datei.
    """
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.2
    }
    
    try:
        req = urllib.request.Request(
            url, 
            data=json.dumps(payload).encode("utf-8"), 
            headers=headers, 
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            raw_data = response.read().decode("utf-8")
            res_data = json.loads(raw_data)
            choices = res_data.get("choices", [])
            if choices and len(choices) > 0:
                content = choices[0].get("message", {}).get("content", "")
                return str(content)
            return json.dumps({"error": "Unerwartetes LLM-Antwortformat"})
    except Exception as e:
        print(f"LLM API-Aufruf fehlgeschlagen: {e}", file=sys.stderr)
        return json.dumps({"error": f"LLM-Aufruf fehlgeschlagen: {e}"})

class AgentLoop:
    root: Path
    env_path: Path
    env: dict[str, str]
    brief_path: Path
    map_path: Path

    def __init__(self, workspace_root: Path) -> None:
        self.root = workspace_root
        self.env_path = self.root / ".env"
        self.env = load_env(self.env_path)
        self.brief_path = self.root / ".context" / "active_brief.md"
        self.map_path = self.root / "gemini.md"
        
    def read_file(self, path: Path) -> str:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    def write_file(self, path: Path, content: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def execute_tool(self, tool_name: str, args: list[str]) -> str:
        """
        Sichere Ausführung von Tools. Blockiert Directory Traversal Angriffe!
        """
        # HÄRTUNG: Nur reine Dateinamen ohne Verzeichnispfade zulassen
        if not re.match(r"^[a-zA-Z0-9_]+$", tool_name):
            return json.dumps({"error": f"Ungültiger Tool-Name '{tool_name}'. Sicherheitsverletzung blockiert!"})

        tool_path = self.root / "tools" / f"{tool_name}.py"
        if not tool_path.exists():
            return json.dumps({"error": f"Tool {tool_name} nicht im tools/ Verzeichnis gefunden."})
            
        cmd = [sys.executable, str(tool_path)] + args
        print(f"Führe aus: {' '.join(cmd)}", file=sys.stderr)
        try:
            full_env = os.environ.copy()
            full_env.update(self.env)
            
            res = subprocess.run(cmd, capture_output=True, text=True, env=full_env, timeout=45)
            if res.returncode != 0:
                return json.dumps({"error": res.stderr})
            return res.stdout
        except Exception as e:
            return json.dumps({"error": str(e)})

    def _append_log_with_rotation(self, gemini_map_content: str, log_entry: str) -> None:
        """
        Fügt Logs an gemini.md an, hält aber die Liste der Logs auf den letzten 10 Einträgen.
        Verhindert ein unendliches Aufblähen des LLM-Kontextfensters!
        """
        section_header = "## 4. Maintenance & Execution Log"
        parts = gemini_map_content.split(section_header)

        header_part = parts[0] + section_header + "
"
        log_part = parts[1] if len(parts) > 1 else ""

        # Extrahiere bestehende Logzeilen
        lines = [line.strip() for line in log_part.split("\n") if line.strip()]
        lines.append(log_entry.strip())

        # Log-Rotation: Behalte nur die letzten 10 Einträge
        rotated_lines = lines[-10:]

        final_content = header_part + "\n" + "\n".join(f"* {line.lstrip('* ')}" for line in rotated_lines) + "\n"
        self.write_file(self.map_path, final_content)

    def run_step(self, user_instruction: str | None = None) -> dict[str, Any]:
        api_key = self.env.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        model_name = self.env.get("BLAST_LLM_MODEL", "gpt-4o-mini")
        
        brief = self.read_file(self.brief_path)
        gemini_map = self.read_file(self.map_path)
        
        system_prompt = (
            "You are the B.L.A.S.T. Navigation Agent (Layer 2). You read the active brief and gemini.md "
            "and suggest the next deterministic python tool (Layer 3) to execute. "
            "You MUST reply ONLY with a JSON block containing:\n"
            "1. 'action': one of ['execute_tool', 'task_complete', 'fail']\n"
            "2. 'tool_name': e.g., 'scraper_opendata_dortmund' or 'inventory_compiler' (without .py extension)\n"
            "3. 'arguments': list of string args to pass to the script\n"
            "4. 'reason': brief explanation of why this step is proposed.\n"
            "Do not include any other markdown prose in your reply, just the JSON block."
        )
        
        user_prompt = f"Active Brief:\n{brief}\n\nProject Map (gemini.md):\n{gemini_map}\n"
        if user_instruction:
            user_prompt += f"\nUser Directive:\n{user_instruction}\n"
            
        print("Sende Anfrage an LLM...", file=sys.stderr)
        if not api_key:
            print("Kein API-Key gefunden. Führe Dry-Run aus...", file=sys.stderr)
            decision_text = json.dumps({
                "action": "execute_tool",
                "tool_name": "scraper_opendata_dortmund",
                "arguments": ["search_datasets", "Bibliotheken"],
                "reason": "Dry-run Simulation ohne Live-Verbindung."
            })
        else:
            decision_text = call_llm(api_key, system_prompt, user_prompt, model_name)
            
        decision_text = decision_text.strip()
        if decision_text.startswith("```"):
            decision_text = decision_text.split("```")[1]
            if decision_text.startswith("json"):
                decision_text = decision_text[4:]
            decision_text = decision_text.strip()
            
        try:
            decision = json.loads(decision_text)
        except Exception as e:
            return {"error": f"Fehler beim Parsen der LLM-Entscheidung: {e}", "raw": decision_text}
            
        action = decision.get("action")
        if action == "execute_tool":
            tool_name = str(decision.get("tool_name", ""))
            args_list = decision.get("arguments", [])
            args = [str(a) for a in args_list] if isinstance(args_list, list) else []
            
            output = self.execute_tool(tool_name, args)
            
            # Log-Eintrag schreiben mit Log-Rotation
            log_entry = f"**{datetime.now(timezone.utc).isoformat()}**: Executed {tool_name} with {args}. Reason: {decision.get('reason')}"
            self._append_log_with_rotation(gemini_map, log_entry)
            
            return {
                "status": "success",
                "tool": tool_name,
                "arguments": args,
                "output": output
            }
        else:
            return {
                "status": "ended",
                "action": action,
                "reason": decision.get("reason")
            }

def main() -> None:
    workspace_root = Path(__file__).resolve().parent.parent
    loop = AgentLoop(workspace_root)
    res = loop.run_step()
    print(json.dumps(res, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
