# A_n g_e_L_a  June 2024

import sys, os
import subprocess
from termcolor import colored
import os.path
from pathlib import Path



SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))
from configs import  config

SAVE_PATH = Path(config.SAVEPATH)
BATCH_DOWNLOAD = config.BATCH_DOWNLOAD

count = 0
title = "Batch Downloader"
strap = "for UK-FTA\n"
print(colored(title, 'green'))
print(colored(strap, 'red'))

print(f"[info] BATCH_DOWNLOAD is set to: {BATCH_DOWNLOAD}")
print("[info] BATCH_DOWNOAD may be set using Config from the menu")
print(f"[info] The location of the batch file is set to:\n{colored(SAVE_PATH, 'red')}")
if os.path.isfile(f"{SAVE_PATH}/batch.txt"):
    print("[info] batch.txt exists")
else:
    print("[info] batch.txt does not exist")
    print("Exiting...")
    exit()


#################################################################
# comment out next four lines to use a sheduled batch download #
#################################################################
   
start = input("Proceed? y/n\n")
if start == 'n':
    print("Exiting...")
    exit()

with open(f"{SAVE_PATH}/batch.txt") as f:
    while True:
        count += 1
        try:
            line = f.readline()
        except:
            break
        command = line.split()
        try:
            subprocess.call(command)
        except:
            break
        if not line:
            break
    f.close()
    print(f"Downloads processed: {count-1}\n")  # tries to process EOF and counts one extra.

    delete = input("Delete batch.txt? y/n\n")
    if delete == 'y':
        os.remove(f"{SAVE_PATH}/batch.txt")
        print("batch.txt deleted")
    try:
        os.remove("./subs.srt")  # delete any orphaned subs.srt
    except:
        pass
    print("Remember to set BATCH_DOWNLOAD to False in the config file")
