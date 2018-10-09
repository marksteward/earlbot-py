.PHONY: init run

run:
	python earlbot.py earlbot.yml

init:
	virtualenv --clear -p python3 env
	env/bin/pip install -r requirements.txt
