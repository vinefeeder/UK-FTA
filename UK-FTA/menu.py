from beaupy import select
import os
import pyfiglet as PF
from rich.console import Console
from ukfta.my5_dl.keys.autohmac import Sethmackey as S

import time



UPDATE = False

def cleanup():
    if os.name == 'posix':
        os.system('clear')
    else:
        os.system('cls')

def underline(text):
    return "\u0332".join(text)

if __name__ == '__main__':
    console = Console()
    title = PF.figlet_format(' UK-FTA ', font='smslant')
    console.print(title, style="green")
    strapline = "Choose Your Search, Selector and Downloader.\n"
    console.print(strapline, style="red")
    strapline = "Which Channel?"
    console.print(strapline, style="green")
    
    ### check C5 timestamp
    time_stamp = int(time.time_ns() // 1_000_000_000)

    file = r"ukfta/my5_dl/config.py"
    lines = open(file, 'r').readlines()
    savedtime = int(lines[3].replace('\n',''))
    if (time_stamp - savedtime) > (3 * 86400):  # 3 days
        #update
        UPDATE = True

mylist = {
    'BBC': "ukfta/bbc_dl/getBBCLinks.py",
    'ITVX': "ukfta/itv_dl/itv_loader.py",
    "All4": "ukfta/c4_dl/chan4_loader.py",
    "My5": "ukfta/my5_dl/my5_loader.py",
    'UKTVPlay': 'ukfta/uktvp/uktvp_loader.py',
    'STV': 'ukfta/stv_dl/stv_loader.py',
    'TPTV': 'ukfta/tptvencore/TalkingPics.py',
    '*': 'menu.py',
    'Config': 'ukfta/config',
    'Update My5': 'ukfta/my5_dl/hmac-aes-update.py',
}

bpl = ['BBC', 'ITVX', 'All4', 'My5', 'UKTVPlay', 'STV', 'TPTV',
       '------',
       'Config', 'Update My5']
want = select(bpl, cursor_index=0, cursor="🢧", cursor_style="cyan", strict=False)
try:
    need = mylist[want]
    if 'Config' in want:
        if os.name == 'posix':
            os.system('nano ukfta/configs/config.py')
        else:
            os.system('notepad.exe  ./ukfta/configs/config.py')
    elif 'Update' in want:
        os.system(f'python {need}')
    elif UPDATE and ('My5' in want):
        S()
        try:
            need = mylist[want]
            cleanup()
            os.system(f"python {need}")
        except:
            cleanup()
    elif '--' in want:
        os.system('python menu.py')
    elif 'Down' in want:
        os.system('python menu.py')
    else:
        need = mylist[want]
        try:
            cleanup()
            os.system(f"python {need}")
        except:
            cleanup()
            
            
except Exception as e:
    print(e)
    #cleanup()
