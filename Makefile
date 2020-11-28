setup:
	sudo python3 setup.py install

init:
	sudo pip install -r requirements.txt

test:
	python3 tests/test_lnk_frame.py

.PHONY: setup init test
