create-venv:
	python3 -m venv venv

activate-venv:
	source venv/bin/activate

install:
	pip install -r requirements.txt

run:
	uvicorn app.main:app
