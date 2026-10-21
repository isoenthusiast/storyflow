.PHONY: test
test:
	python3 -m unittest discover -s tests -v
	python3 -m py_compile webapp/server.py tools/backup.py tools/demo.py
	node --check webapp/app.js
