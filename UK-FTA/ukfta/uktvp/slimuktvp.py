# A_n_g_e_l_a  revised June 2024
import re, os , sys
import httpx
from httpx import Client
from rich.console import Console
import subprocess
from pathlib import Path
from termcolor import colored
import pyfiglet as PF
import time
from beaupy.spinners import *

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))
from configs import  config

WVD_PATH = config.WVDPATH
SAVE_PATH = config.SAVEPATH
PYWIDEVINE = True
BATCH_DOWNLOAD = config.BATCH_DOWNLOAD

OUT_PATH = Path(SAVE_PATH)

try:
    OUT_PATH.mkdir(exist_ok=True, parents=True)
except:
    print("Error creating save directory. Have you set up your save folder from Config in the menu?")

client = Client()
console = Console()

pk = "BCpkADawqM3mRF3li7oN1VwF3bfyxCYv583LL7PXT9gsFqMM98mgjUBmr0i_q0HXahTvuoeLpXIzODv4n7wjaErBpIWJ3oPQvFQ298UdE8e2mKl_-EYP8CKk8OkovAM6c8XhZgz4o9SckCamNkocUu4H1pJL5yL4UtY7RA"

    
def pad_number( match):
    number = int(match.group(1))
    return format(number, "02d")

def get_pssh(mpd_url):
    mpd = client.get(mpd_url).text
    lines = mpd.split("\n")
    for line in lines:
        m = re.search('<cenc:pssh>(AAAA.+?)</cenc:pssh>', line) 
        if m:
            pssh = m.group(1)
    return pssh

# use wvd
def get_keys(pssh, license_url):
    if PYWIDEVINE:
        from pywidevine.cdm import Cdm
        from pywidevine.device import Device
        from pywidevine.pssh import PSSH

        device = Device.load(WVD_PATH)
        cdm = Cdm.from_device(device)
        session_id = cdm.open()

        challenge = cdm.get_license_challenge(session_id, PSSH(pssh))
        response = httpx.post(license_url, data=challenge)
        cdm.parse_license(session_id, response.content)
        keys = []
        #keys = [key.key.hex() for key in cdm.get_keys(session_id) if key.type != 'SIGNING']
        for key in cdm.get_keys(session_id):
            if key.type == 'CONTENT':
                keys.append(f"{key.kid.hex}:{key.key.hex()}")

    cdm.close(session_id)
    return "\n".join(keys)


def download(url):
    response = client.get(url,follow_redirects=True)
    videoid = (url.split('?')[0]).split('/')[7]
    videonamesplit = url.split('/',7) 
    title =  videonamesplit[4].title()    
    videoname = videonamesplit[4]+videonamesplit[5]+videonamesplit[6]
    videoname = videoname.replace('series-','_S').replace('episode-', 'E')
    videoname = re.sub(r"(\d+)", pad_number, videoname).title()
    headers = {
    'Accept': f"application/json;pk={pk}",
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1788.0',
    'Accept-Language': 'en-GB,en;q=0.5',
    'Origin': 'https://uktvplay.co.uk',
    'Host': 'edge.api.brightcove.com',
    'Referer': f"{url}?loginComplete=true&autoplaying=true",
    }
    response = client.get(
    f'https://edge.api.brightcove.com/playback/v1/accounts/1242911124001/videos/{videoid}',                                                                          
    headers=headers)
    myjson = response.json() 
    #console.print_json(data=myjson)
    #sources►2►src
    mpd_url = myjson['sources'][2]['src']
    #sources►2►key_systems►com.widevine.alpha►license_url
    lic_url = myjson['sources'][2]['key_systems']['com.widevine.alpha']['license_url']
    pssh = get_pssh(mpd_url)
    key = get_keys(pssh, lic_url)
    #print(f"Keys: {key}"   )


    m3u8dl = 'N_m3u8DL-RE'

    command = [
        m3u8dl,
        mpd_url,
        '--key',
        key,
        '--auto-select',
        '--save-name',
        videoname,
        '--save-dir',
        f"{OUT_PATH}/UKTVP/{title}",
        '--tmp-dir',
        './',
        '-M',
        'format=mkv:muxer=mkvmerge',
        '--no-log',
    ]

    cleaned_command = [cmd.replace('\n', ' ').strip() for cmd in command]

    if BATCH_DOWNLOAD:
        with open(f'{SAVE_PATH}/batch.txt', 'a') as f:
            print(f"Added {title} to batch file.")
            f.write(' '.join(cleaned_command) + '\n')
    else:
        # print(command)
        subprocess.run(command)
        print(f"File saved to {OUT_PATH}/{title}")

def cleanup():
    ###############################################################################################
    # The beaupy module that produces checkbox lists seems to clog and confuse my linux box's terminal; 
    # I do a reset after downloading.
    # if that is not what you want, as it may remove any presets, comment out the 'if' phrase below
    # Note: Only resets unix boxes
    ###############################################################################################
    if os.name == 'posix':
        spinner = Spinner(CLOCK, "[info] Preparing to reset Terminal...")
        spinner.start()
        time.sleep(5)
        spinner.stop()     
        os.system('reset')
def run():
    url = input("Enter a video URL to download: ")
    download(url)
    cleanup()
    exit(0)

if __name__ == "__main__":
    title = PF.figlet_format(' U ', font='smslant')
    print(colored(title, 'green'))
    strapline = "A Single U Downloader:\n\n"
    print(colored(strapline, 'red'))
    run()
    
