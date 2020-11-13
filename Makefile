setup:
	sudo python3 setup.py install

init:
	sudo pip install -r requirements.txt

#test:
#	py.test tests

.PHONY: setup init test
