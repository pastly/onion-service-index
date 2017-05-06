#!/usr/bin/env bash
VENV=./venv
if ! mkdir -v $VENV
then
	echo $VENV seems to alrady exist. If you\'re having trouble, consider
	echo deleting it before running this script again.
	exit 1
fi
virtualenv-3 $VENV
pip3 install flask
echo execute \"source $VENV/bin/activate\" to enter virtual environment
echo execute \"deactivate\" to exit virtual environment

