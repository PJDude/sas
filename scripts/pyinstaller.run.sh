#!/bin/bash

dir="$(readlink -m $(dirname "$0"))"
cd $dir/../src

VERSION=`cat ./version.txt`
VERSION=${VERSION:1:10}
echo VERSION=$VERSION

outdir=../build-pyinstaller$venvname

rm -rf $outdir
mkdir $outdir

echo ''
echo running-pyinstaller
echo wd:`pwd`

echo `python3 --version` > distro.info.txt
echo '' >> distro.info.txt
echo pyinstaller `pyinstaller --version` >> distro.info.txt
echo "numpy       " `python3 -c "import numpy; print(numpy.__version__)"` >> distro.info.txt
echo "sounddevice " `python3 -c "import sounddevice; print(sounddevice.__version__)"` >> distro.info.txt

echo ''

echo running-pyinstaller
#--onefile
pyinstaller \
     --strip --noconfirm --noconsole --clean --add-data="distro.info.txt:." --add-data="version.txt:." --add-data="../LICENSE:." --contents-directory=internal --distpath=$outdir --additional-hooks-dir=. --optimize 2 ./sas.py

echo ''
echo packing
cd $outdir
zip -9 -r -m ./sas.lin.zip ./sas
