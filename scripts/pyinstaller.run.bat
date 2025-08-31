@cd "%~dp0.."
@echo building with pyinstaller
@cd src

@set /p VERSION=<version.txt
@SET VERSION=%VERSION:~1,10%
@echo VERSION=%VERSION%

@SET OUTDIR=..\build-pyinstaller

@if exist %OUTDIR% rmdir /s /q %OUTDIR%
@mkdir %OUTDIR%

@echo.
@echo running-pyinstaller
@echo wd:%CD%

@python --version > distro.info.txt
@echo. >> distro.info.txt
@echo|set /p="pyinstaller " >> distro.info.txt
@pyinstaller --version >> distro.info.txt
@echo|set /p="numpy       " >> distro.info.txt
@python -c "import numpy; print(numpy.__version__)" >> distro.info.txt
@echo|set /p="sounddevice " >> distro.info.txt
@python -c "import sounddevice; print(sounddevice.__version__)" >> distro.info.txt

@echo.
@echo running-pyinstaller
pyinstaller --version-file=version.pi.txt --noconfirm --clean --add-data="distro.info.txt:." --add-data="version.txt;." --add-data="../LICENSE;." --icon=icon.ico --distpath=%OUTDIR% --windowed --contents-directory=internal --additional-hooks-dir=. --optimize 2 sas.py  || exit /b 2

@echo.
@echo packing
powershell Compress-Archive %OUTDIR%\sas %OUTDIR%\sas.win.zip
