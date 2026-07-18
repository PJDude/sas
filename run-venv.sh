#!/bin/sh

venv_folder=venv_temp

python3 -m venv $venv_folder

source $venv_folder/bin/activate

python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

cd ./src
. ../scripts/icons.convert.sh
. ../scripts/version.gen.sh
python3 ./sas.py

