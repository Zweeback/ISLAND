import os
import sys
import json
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

try:
    from local_llm_bridge import query_ollama
except ImportError:
    # Handle cases where agent_loop is called directly and the import path isn't right
    from tools.local_llm_bridge import query_ollama

def call_llm(api_key: str, system_prompt: str, user_prompt: str) -> str:
    """
    Direct HTTP request to OpenAI Chat Completions API using urllib.
    Requires no external packages. Returns JSON text or error string.
    """
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": "gpt-4o-mini",
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
            if choices and isinstance(choices, list) and len(choices) > 0:
                first_choice = choices[0]
                if isinstance(first_choice, dict):
                    message = first_choice.get("message", {})
                    if isinstance(message, dict):
                        content = message.get("content", "")
                        return str(content)
            return json.dumps({"error": "Unexpected LLM response format"})
    except Exception as e:
        print(f"LLM API Call failed: {e}", file=sys.stderr)
        return json.dumps({"error": f"LLM Call failed: {e}"})

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
        Executes a Python tool under tools/ via subprocess.
        """
        tool_path = self.root / "tools" / f"{tool_name}.py"
        if not tool_path.exists():
            return json.dumps({"error": f"Tool {tool_name} not found"})
            
        cmd = [sys.executable, str(tool_path)] + args
        print(f"Executing: {' '.join(cmd)}", file=sys.stderr)
        try:
            full_env = os.environ.copy()
            full_env.update(self.env)
            
            res = subprocess.run(cmd, capture_output=True, text=True, env=full_env, timeout=30)
            if res.returncode != 0:
                return json.dumps({"error": res.stderr})
            return res.stdout
        except Exception as e:
            return json.dumps({"error": str(e)})

    def run_step(self, user_instruction: str | None = None) -> dict[str, Any]:
        api_key = self.env.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        
        # Read files for LLM context
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
            
        use_local_llm = self.env.get("USE_LOCAL_LLM", "false").lower() == "true"

        print("Reasoning with LLM...", file=sys.stderr)
        if use_local_llm or not api_key:
            print("Using local Ollama model for reasoning...", file=sys.stderr)
            decision_text = query_ollama(system_prompt, user_prompt)
            # If Ollama returns an error and no API key is present, fallback to dry-run
            if "error" in decision_text and not api_key:
                print("Local LLM failed and no OpenAI API key found, running dry-run mode...", file=sys.stderr)
                decision_text = json.dumps({
                    "action": "execute_tool",
                    "tool_name": "scraper_opendata_dortmund",
                    "arguments": ["search_datasets", "Bibliotheken"],
                    "reason": "OpenData Dortmund API is public and does not require credentials. Let's do a public dry-run search."
                })
        else:
            decision_text = call_llm(api_key, system_prompt, user_prompt)
            
        # Clean potential markdown fences
        decision_text = decision_text.strip()
        if decision_text.startswith("```"):
            decision_text = decision_text.split("```")[1]
            if decision_text.startswith("json"):
                decision_text = decision_text[4:]
            decision_text = decision_text.strip()
            
        try:
            decision = json.loads(decision_text)
        except Exception as e:
            return {"error": f"Failed to parse LLM decision JSON: {e}", "raw": decision_text}
            
        action = decision.get("action")
        if action == "execute_tool":
            tool_name = str(decision.get("tool_name", ""))
            args_list = decision.get("arguments", [])
            args = [str(a) for a in args_list] if isinstance(args_list, list) else []
            
            # Execute tool
            output = self.execute_tool(tool_name, args)
            
            # Update log in gemini.md
            log_entry = (
                f"\n* **{datetime.now(timezone.utc).isoformat()}**: Executed {tool_name} with {args}. "
                f"Reason: {decision.get('reason')}\n"
            )
            self.write_file(self.map_path, gemini_map.rstrip() + "\n" + log_entry)
            
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
    workspace_root = Path(__file__).parent.parent.resolve()
    loop = AgentLoop(workspace_root)
    res = loop.run_step()
    print(json.dumps(res, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
