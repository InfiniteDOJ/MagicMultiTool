# Guide on how to install this:

# Windows(Only use this if the MagicChabox App will NOT work)

  ```pip install flask python-osc waitress```

 ## Once you got "Python-osc" installed you wanna make a folder where ever you want(in this case ill be using desktop)
 ## you wanna make a file called "Start_MagicMultiTool"
  ```
  @echo off
title MagicMultiTool Server
cd /d "%~dp0"
echo Starting MagicMultiTool...
start http://localhost:5000
python app.py
pause
  ```
### Enable the view file extenions option... search online how to.

### Also forgot to mention, you __NEED__ Python so install python [Here](https://www.python.org/downloads/release/python-3146/)

## and now just run the batch file

# Mac OS Guide

## Open terminal by pressing "Cmd + Space"

## Once done install this:

  ```pip3 install flask python-osc waitress```

## NOTE: Go to [Here](https://www.python.org/downloads/release/python-3146/) and install python before running the command above

## Open the TextEdit app. Go to Format -> Make Plain Text. Paste the code below

  ```
  #!/bin/bash
cd "$(dirname "$0")"
echo "Starting MagicMultiTool..."
open http://localhost:5000
python3 app.py
  ```

## and then save the file as Start_MagicMultiTool.command(uncheck "If no extension is provided, use .txt")

## also you got to make a folder the exact same name
  ```MagicMultiTool```
## and then run 

  ```chmod +x Start_MagicMultiTool.command```
## and then click enter

### this is optional(only do this if it does not execute in the terminal)
### Double Click "Start_MagicMultiTool.command" 

# Linux Guide
### Note: This only works on debian due to ubunto's hard coded os

## Open up terminal and paste

  ```sudo apt update && sudo apt install python3 python3-pip python3-venv -y```

## Once you ran that command you wanna Make a folder called "MagicMultiTool and make a .sh file called "MagicMultiTool.sh":

  ```
  #!/bin/bash
cd "$(dirname "$0")"
echo "Starting MagicMultiTool Setup..."

# Create a virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "First time setup: Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install flask python-osc waitress
else
    source venv/bin/activate
fi

echo "Starting server..."
xdg-open http://localhost:5000 &
python3 app.py
  ```
## Open up the terminal and paste this:

  ```chmod +x MagicMultiTool.sh```

# Thats the end of the guide.. i hope yall enjoy my open source port for magicchatbox for vrchat

#### Little Update:

## Set up the virtual environment using

 ```python3 -m venv venv```

## Activate the virtual environment

  #### Windows: venv\Scripts\activate
  #### MacOS/Linux: source venv/bin/activate

## When done install flask

  ```pip install flask```
  ##### Also if that dont work try pip3 insted of pip

## And then run the .sh or .bat
