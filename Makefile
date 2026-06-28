.PHONY: test lint compile verify smoke

test:
	python3 -m pytest -q

lint:
	python3 -m ruff check .

compile:
	python3 -m compileall -q .

verify: test lint compile

smoke:
	python3 scripts/smoke.py --vault /home/hermesadmin/Obsidian
