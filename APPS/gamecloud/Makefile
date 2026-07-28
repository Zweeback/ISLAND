.PHONY: install test lint run

install:
	pip install -r requirements.txt

test:
	PYTHONPATH=$(CURDIR) pytest tests/ -v

lint:
	flake8 src/ tests/ --max-line-length=100

run:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

status:
	@python -c "from src.llm.router import LLMRouter; import json; print(json.dumps(LLMRouter().status(), indent=2))"
