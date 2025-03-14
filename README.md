Note: Windows users. Use 'Terminal' from the Microsoft Store instead of the cmd window. It produces far less problems and just works.
## Requirements
* Python 3.10 and upwards.
* pip
* ffmpeg (https://github.com/FFmpeg/FFmpeg) https://www.videohelp.com/software/ffmpeg  or Linux distro
* mp4decrypt (https://github.com/axiomatic-systems/Bento4) -> binary download https://www.bento4.com/downloads/
* N-m3u8DL-RE https://github.com/nilaoda/N_m3u8DL-RE/releases
* MKVMerge from MKVToolNix  https://mkvtoolnix.download/downloads.html  https://www.videohelp.com/software/MKVToolNix
* Shaka-packager  https://github.com/shaka-project/shaka-packager/releases  rename the binary to shaka-packager 
NOTE WINDOWS ONLY: Use packager version 3.1.0 (2024-05-03) as 3.2.0 is flawed.

* Subby for converting subtitles. This is an optional install. 
In most cases ffmgeg or N_m3u8DL-RE do the subtitle conversion in UK-FTA 
but some substitles, notably from STV's back catalogue, do not convert well.
Subby will correct some errors:
subby is installed - in Terminal -  by:-
	git clone https://github.com/vevv/subby.git
	cd subby
	pip install .    (note the full stop)
On windows the cloning agent - git - may need installing before subby may be downloaded (cloned).
See https://git-scm.com/download/win to download an installer.

**This version is incomplete it needs a Content Decryption Module before a video may be decrypted**
* !!!YOU WILL NEED!!! A CDM (device_private_key and device_client_blob) pointed to by a wvd file https://forum.videohelp.com/threads/411862-Beyond-WKS-KEYS

Note a working CDM is NOT installed with UK-FTA
* get_iplayer see https://github.com/get-iplayer/get_iplayer/releases

* On Linux or  Windows the above binary files need to be in your System's PATH
* On Windows a config file needs notepad and Linux uses nano


##  Install
```
It is generally recommended (and now enforced on many systems) to run python scripts
in their own environment.
See https://forum.videohelp.com/threads/411862-Beyond-WKS-KEYS
Briefly:
    python3 -m venv env  # (or however you call python),  run from a folder that contains UK-FTA i.e. one level above.
    # make the env(ironment) active
    source env/bin/activate  # linux
    .\env\Scripts\activate   # windows

On windows, if you have errors with module not found, try reinstalling requirements.txt and upgrading...
python -m pip intall - r requirements.txt --upgrade
Then in the top level folder remove the folder __pycache__/ so it  will be recreated.

Modules needed:
    You may either run the 'runonce.py' python file in UK-FTA folder 'python runconce.py' or by
    pip install -r requirements.txt from the command line
    or to upgrade all modules
    pip install -r requirements.txt --upgrade
```
## config
**Be sure to configure your save path before running this suite of scripts**
Choose the config option in menu.py and alter my example save path to your own use / in your path on all systems
edit the paths therein for your system.
NOTE: A working CDM is included. No configuration is needed.

**My5 will need further configuration before running.**
My5 HMAC and AES should be first updated by selecting 'Update My5' button.
This is a weekly task befor e downloading My5 content

## Usage

```
python gui.py

At first use check the configuration in config - particularly the save-path.
Additionally the config file contains a switch - BATCH_DOWNLOAD ~ either True or False
Set to True download will be deferred until the Batch Download menu button is clicked.
If you wish to use your own scheduler to start UK-FTA/ukfta/getbatch.py edit the getbatch.py 
where advised.

Ev
``
## Addendum
There is a backup method for getting my5 HMAC-SECRET and AES-KEY as an option in the menu. 
Normally it will not need to be used.

If ever the website that hosts current HYMAC and AES data goes down, then use the updater here.
If you get errors from Selenium complaining of 'No Driver Found' then be sure to create a python environment first.
See https://forum.videohelp.com/threads/411862-Beyond-WKS-KEYS and the section 'Running python scripts in a special Python environment', and set up an environment in which UK-FTA will run. It keeps all UK-FTA modules separate from other scripts you may have on your system.

*Note: Talking Pictures TV does not work in batch mode.
