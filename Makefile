.PHONY: test lint typecheck dev engine worker

test:
	python -m pytest tests/ -v --tb=short

lint:
	npm run lint

typecheck:
	npx tsc --noEmit

dev:
	npm run dev

engine:
	python python/main.py

worker:
	python -m python.workers.collector_worker
