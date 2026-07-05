with open("08_TOOLS_SCRIPTS/blast_agent/tests/test_blast_agent.py", "r") as f:
    content = f.read()
content = content.replace('assert "Error: Scraper scraper_nonexistent.py not found." in captured.err', 'assert "Error: Invalid scraper name \'nonexistent\'." in captured.err')
with open("08_TOOLS_SCRIPTS/blast_agent/tests/test_blast_agent.py", "w") as f:
    f.write(content)
