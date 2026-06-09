.PHONY: dev build test test-py test-fe test-e2e clean

dev:
	cd frontend && npm run dev -- --port 5173 & \
	python3 -m granola_sync --frontend-url http://localhost:5173

build:
	cd frontend && npm install && npm run build
	rm -rf src/granola_sync/_frontend
	cp -r frontend/dist src/granola_sync/_frontend

test: test-py test-fe

test-py:
	python3 -m pytest tests/ -v

test-fe:
	cd frontend && npm test

test-e2e:
	cd frontend && npx playwright test

clean:
	rm -rf frontend/node_modules frontend/dist
	find . -name "__pycache__" -type d -exec rm -rf {} +
