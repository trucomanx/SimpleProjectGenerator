#!/usr/bin/python3

'''
## ubuntu ##
python3 -m venv venv-temporal
source venv-temporal/bin/activate
pip install --upgrade pip

## windows ##
python -m venv venv-temporal
venv-temporal\Scripts\activate
python -m pip install --upgrade pip


pip install pyinstaller pyinstaller-hooks-contrib
pip install -r requirements.txt
cd src


## ubuntu ##
python3 -m PyInstaller --onefile --windowed --name simple_project_generator --add-data "simple_project_generator/icons:icons" --add-data "simple_project_generator/data:data" --collect-all PyQt5  program_launcher.py

## windows ##
python -m PyInstaller --onefile --windowed --name simple_project_generator --add-data "simple_project_generator/icons;icons" --add-data "simple_project_generator/data;data" --collect-all PyQt5  program_launcher.py

'''

from simple_project_generator.program import main
import os

if __name__ == "__main__":
    os.environ["QT_QPA_PLATFORM"] = "xcb"
    main()

