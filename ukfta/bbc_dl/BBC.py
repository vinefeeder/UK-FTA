
import sys
import os
from beaupy.spinners import *
import re
import pyfiglet as PF
from termcolor import colored
import subprocess
import time
from pathlib import Path
from glob import glob

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))
from configs import  config

SAVE_PATH = config.SAVEPATH
BATCH_DOWNLOAD = config.BATCH_DOWNLOAD

def dodownload(videoname):
    ISM = False
    mytext = open('stream.txt', 'r')
    mylines = mytext.readlines()
    for line in mylines:
        if line.startswith('streamurl'):
            if '.ism' in line and not ISM :
                #print(line)
                url = line
                url = url.lstrip('streamurl:     ')
                ISM = True
            if ISM:
                break
    OUT_PATH = Path(f'{SAVE_PATH}/BBC/')
    try:
        OUT_PATH.mkdir(exist_ok=True, parents=True)
    except:
        print("Error creating directory. Have you set up your save folder from Config in the menu?")
    out_path = str(OUT_PATH)
    m3u8dl = 'N_m3u8DL-RE'
    command = [
        m3u8dl,
        url,
        '--append-url-params',
        '--auto-select',
        '--binary-merge',
        '--save-name',
        videoname,
        '--save-dir',
        out_path,
        '--tmp-dir',
        './',
        '--mux-import',
        'path=subs.srt:lang=eng:name="English"',    
        '-M',
        'format=mkv:muxer=mkvmerge',
    ]
    cleaned_command = [cmd.replace('\n', ' ').replace('--mux-import','').replace('path=subs.srt:lang=eng:name="English"','').strip() for cmd in command]

    if BATCH_DOWNLOAD:
        with open(f'{SAVE_PATH}/batch.txt', 'a') as f:
            f.write(' '.join(cleaned_command) + '\n')
    else:
        # print(command)
        subprocess.run(command)
        print(f"File saved to {out_path}/{videoname}")

def pad_number( match):
    number = int(match.group(1))
    return format(number, "02d")

def run():
    url = input("Enter video url for download. \n")
    if 'episodes' in url:
        print("That url is for series download.\n\
        Use the BBC Series option\n\
        from the menu") 
        exit(0)
    pid = url.split('/')[5]
    vname = url.split('/')[-1]
    try:
        vname1 = vname.split('-series-')[0]
        series = pad_number(re.search(r"series-(\d{1,2})", vname))
        episode = pad_number(re.search(r"episode-(\d{1,2})", vname))
        vname1 = vname1.title() + '_S' + series
        vname2 = 'E' + episode
        videoname = vname1 + vname2
    except:
        videoname = vname.split('?')[0].title()
    videoname = videoname.replace('-', '_')
    spinner = Spinner(DOTS)
    spinner.start()
    os.system(f"get_iplayer --nocopyright --output ./ --streaminfo --pid {pid} >> stream.txt")
    os.system(f"get_iplayer --nocopyright --output  ./  --subtitles-only --pid {pid} ")
    for f in glob('*.srt'):
            os.rename( f, "subs.srt")
    spinner.stop()
    dodownload(videoname)



    #clean up
    if  os.path.exists('stream.txt'):
        os.remove('stream.txt')

    if os.name == 'posix': 
        spinner = Spinner(CLOCK, "[info] Preparing to reset Terminal...")
        spinner.start()
        time.sleep(5)
        spinner.stop()     
        os.system('reset')

if __name__ == '__main__':
    title = PF.figlet_format(' B B C', font='smslant')
    print(colored(title, 'green'))
    strapline = "A BBC Single Video Downloader:\n\n"
    print(colored(strapline, 'red'))#
    run()
