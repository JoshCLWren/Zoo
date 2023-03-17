run:
	python main.py

venv:
	pyenv install 3.11.2 --skip-existing
	-pyenv uninstall -f zoo_venv
	-pyenv virtualenv 3.11.2 zoo_venv
	pyenv local zoo_venv
	pip install --upgrade pip
	pip install --upgrade pip-tools

cov:
	pytest --cov=.  --cov-report html:htmlcov && open htmlcov/index.html

lint-fix:
	black .
	isort .
