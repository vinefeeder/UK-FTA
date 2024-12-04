# A_n_g_e_l_a  modified 26:10:2023 to use N_m3u8DL-RE
# grunt work getting My5-keys is by Diazole, with grateful thanks

# The file config.py contains a hmac-secret and an aes key. 
# These change regularly. Diazole produced an html file which when loaded
# into yor browser produced the hmac-secret and eas.key
# There is a script you may also run which will get the hmac and key and enter
# the results into config.py
# see the instructions inside hmac-aes-update.py

import base64
from Crypto.Cipher import AES
import re
import json
import time
import hmac
import hashlib
import requests
from rich.console import Console
import os, subprocess, re, sys
from pywidevine.pssh import PSSH
from pywidevine.device import Device
from pywidevine.cdm import Cdm
from urllib.parse import urlparse
import pyfiglet as PF
from termcolor import colored
from beaupy.spinners import *
import time
from pathlib import Path


import sys
import os.path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from configs import  config  #global

from my5_dl.config import (
    AES_KEY,
    APP_NAME,
    BASE_URL_MEDIA,
    BASE_URL_SHOWS,
    DEFAULT_HEADERS,
    DEFAULT_JSON_HEADERS,
    HMAC_SECRET,
    TMP_DIR,
    
)



WVD_PATH = config.WVDPATH
SAVE_PATH = config.SAVEPATH
DOWNLOAD_DIR = Path(SAVE_PATH)
try:
    DOWNLOAD_DIR.mkdir(exist_ok=True, parents=True)
except:
    print("Error creating save directory. Have you set up your save folder from Config in the menu?")
DOWNLOAD_DIR = f"{DOWNLOAD_DIR}/MY5"
BATCH_DOWNLOAD = config.BATCH_DOWNLOAD


def generate_episode_url(url):
 
    try:
        print("Generating the episode URL...")
        path_segments = urlparse(url).path.strip("/").split("/")

        if path_segments[0] != "show":
            return

        if len(path_segments) == 2:
            show = path_segments[1]
            return f"{BASE_URL_SHOWS}/{show}/episodes/next.json?platform=my5desktop&friendly=1"
        if len(path_segments) == 4:
            show = path_segments[1]
            season = path_segments[2]
            episode = path_segments[3]
            return f"{BASE_URL_SHOWS}/{show}/seasons/{season}/episodes/{episode}.json?platform=my5desktop&friendly=1&linear=true"
        return None
    except Exception as ex:
        print(f"[!] Exception thrown when attempting to get the episode URL: {ex}")
        raise

def decrypt_content(content):
    try:
        print("Decrypting the content response...")
        key_bytes = base64.b64decode(AES_KEY)
        iv_bytes = base64.b64decode(b64_url_to_std(content["iv"]))
        cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
        data_bytes = base64.b64decode(b64_url_to_std(content["data"]))
        decrypted_data = cipher.decrypt(data_bytes)
        #shallow-copy [:] -> to slices, remove last slice -> [-1] and decode to str
        return decrypted_data[: -decrypted_data[-1]].decode()

    except Exception as ex:
        print(f"[!] Exception thrown when attempting to decrypt the content info: {ex}")
        raise

def b64_url_to_std(val):
    replacements = [
        (r"\u002d", "+"),
        (r"\x5f", "/"),
    ]
    for pattern, repl in replacements:
        val = re.sub(pattern, repl, val, 0)
    return val

def b64_std_to_url(val):
    replacements = [
        (r"\+", "-"),
        (r"\/", "_"),
        (r"=+$", ""),
    ]
    for pattern, repl in replacements:
        val = re.sub(pattern, repl, val, 0)
    return val

def generate_content_url(content_id):
    try:
        print("Generating the content URL...")
        timestamp = int(time.time())
        c_url = f"{BASE_URL_MEDIA}/{APP_NAME}/{content_id}.json?timestamp={timestamp}"
        sig = hmac.new(base64.b64decode(HMAC_SECRET), c_url.encode(), hashlib.sha256)
        auth = base64.b64encode(sig.digest()).decode()
        return f"{c_url}&auth={b64_std_to_url(auth)}"
    except Exception as ex:
        print(f"[!] Exception thrown when attempting to get the content URL: {ex}")
        raise

def get_content_info(episode_url):
    try:
        print("Getting the encrypted content info...")
        r = requests.get(episode_url, headers=DEFAULT_JSON_HEADERS, timeout=10)
        if r.status_code != 200:
            print(
                f"[!] Received status code '{r.status_code}' when attempting to get the content ID"
            )
            return

        resp = json.loads(r.content)

        if resp["vod_available"] == False:
            print("[!] Episode is not available")
            return

        return (
            resp["id"],  #content_id
            resp["sea_num"],
            str(resp["ep_num"]),
            resp["sh_title"],
            resp["title"],
        )
    except Exception as ex:
        print(f"[!] Exception thrown when attempting to get the content ID: {ex}")
        raise

def get_content_response(content_url):
    try:
        print("Getting content response...")
        r = requests.get(content_url, headers=DEFAULT_JSON_HEADERS, timeout=10)
        if r.status_code != 200:
            print(
                f"[!] Received status code '{r.status_code}' when attempting to get the content response"
            )
            return
        resp = json.loads(r.content)
        return json.loads(decrypt_content(resp))
    except Exception as ex:
        print(f"[!] Exception thrown when attempting to get the content response: {ex}")
        raise

def get_rendition(decrypted_content):
    try:
        for asset in decrypted_content["assets"]:
            if asset["drm"] == "widevine":
                lic_url = asset['keyserver']
                print("[LICENSE URL]", lic_url)
                original_mpd = asset["renditions"][0]["url"]
                print(original_mpd)
                content_id = decrypted_content["id"]
                mpd_pattern = re.compile(rf"{content_id}[^/]*\.mpd$")

                # Replace the ending part to get default and subtitles MPD URLs
                default_mpd = mpd_pattern.sub(f'{content_id}.mpd', original_mpd)
                subtitles_mpd = mpd_pattern.sub(f'{content_id}_subtitles.mpd', original_mpd)

                # Handle cases where subtitles are not present
                if default_mpd == original_mpd:
                    subtitles_mpd = None

                print("[DEFAULT MPD URL]", default_mpd)
                print("[SUBTITLES URL]", subtitles_mpd)
    except Exception as e:
        print(f"An error has occurred. Is the AES key and the HMAC secret up-to-date?\n\
               The error message was:\n{e}")

    return (
        lic_url,
        default_mpd,
        subtitles_mpd,
    )
def get_pssh_from_mpd(mpd: str):
    try:
        print("Extracting PSSH from MPD...")
        r = requests.get(mpd, headers=DEFAULT_JSON_HEADERS, timeout=10)
        if r.status_code != 200:
            print(
                f"[!] Received status code '{r.status_code}' when attempting to get the MPD"
            )
            return

        return re.findall(r"<cenc:pssh>(AAAA.*?)</cenc:pssh>", r.text)[1]
    except Exception as ex:
        print(f"[!] Exception thrown when attempting to get the content ID: {ex}")
        raise

def get_decryption_key(pssh: str, lic_url):
    cdm = None
    session_id = None
    try:
        print("Getting decryption keys...")

        device = Device.load(WVD_PATH)
        cdm = Cdm.from_device(device)
        session_id = cdm.open()
        challenge = cdm.get_license_challenge(session_id, PSSH(pssh))
        r = requests.post(lic_url, data=challenge, headers=DEFAULT_HEADERS, timeout=10)
        if r.status_code != 200:
            print(
                f"[!] Received status code '{r.status_code}' when attempting to get the license challenge"
            )
            return
        cdm.parse_license(session_id, r.content)

        decryption_key = None
        for key in cdm.get_keys(session_id):
            if key.type == "CONTENT":
                if decryption_key is None:
                    decryption_key = f"{key.kid.hex}:{key.key.hex()}"
                print("[KEY]", f"{key.kid.hex}:{key.key.hex()}")
        return decryption_key
    except Exception as ex:
        print(f"[!] Exception thrown when attempting to get the decryption keys: {ex}")
        raise
    finally:
        cdm.close(session_id)

def pad_number(match):
    number = int(match.group(1))
    return format(number, "02d")

def rinse(string):
        illegals = "*'%$!(),.;"  # safe for urls
        string = ''.join(c for c in string if c.isprintable() and c not in illegals)
        replacements = {
            ' ': '_',
            '_-_': '_',
            '&': 'and',
            ':': '',
        }
        for rep in replacements:  
            string = string.replace(rep, replacements[rep])
        return string

def check_required_config_values() -> None:
    lets_go = True
    if not HMAC_SECRET:
        print("HMAC_SECRET not set")
        lets_go = False
    if not AES_KEY:
        print("AES_KEY not set")
        lets_go = False
    if not WVD_PATH:
        print("WVD_PATH not set")
        lets_go = False
    if WVD_PATH and not os.path.exists(WVD_PATH):
        print("WVD file does not exist")
    if not lets_go:
        sys.exit(1)

def get_streams(mpd ,key, show_title, full_title):
    command = [
        "N_m3u8DL-RE",
        mpd,
        "--auto-select",
        "--save-name",
        full_title,
        "--save-dir",
        f"{DOWNLOAD_DIR}/{show_title}",
        "--tmp-dir",
        f"{TMP_DIR}",
        '--check-segments-count',
        'False',
        "-mt",
        "--use-shaka-packager",
        "--key",
        key,
        "-M",
        "format=mkv:muxer=mkvmerge",
        "--no-log"
        ]
    cleaned_command = [cmd.replace('\n', ' ').strip() for cmd in command]


    if BATCH_DOWNLOAD:
        with open(f'{SAVE_PATH}/batch.txt', 'a') as f:
            f.write(' '.join(cleaned_command) + '\n')
    else:
        # print(command)
        subprocess.run(command)
        print(f"File saved to {DOWNLOAD_DIR}/{show_title}")


def main(url):
    print(url)
    #exit(0)
    check_required_config_values()
    url = url.encode('utf-8', 'ignore').decode().strip()
    episode_url = generate_episode_url(url)

    ( content_id,
    season, 
    episode, 
    show_title,
    episode_title ) =get_content_info(episode_url)
    show_title = rinse(show_title)
    show_title = show_title.replace('?','')
    episode_title = rinse(episode_title)
    if 'Episode' in episode_title:
        episode_title = ""
    if season:
        season = re.sub(r"(\d+)", pad_number, season)
    else:
        season = '00'
    episode = re.sub(r"(\d+)", pad_number, episode)
    if not episode_title == "":
        if show_title in episode_title:
            full_title = f"{show_title}_S{season}E{episode}"
        else:
            full_title = f"{show_title}_[{episode_title}]_S{season}E{episode}"
    else:
        full_title = f"{show_title}_S{season}E{episode}"
    content_url = generate_content_url(content_id)
    decrypted_message = get_content_response(content_url)
    try:
        lic, mpd, subs = get_rendition(decrypted_message)
    except:
        lic, mpd = get_rendition(decrypted_message)
        subs = None
    pssh = get_pssh_from_mpd(mpd)
    key = get_decryption_key(pssh, lic)
    get_streams(mpd, key, show_title, full_title)
    
    return
    
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
    return

# Entry point
def run():
    title = PF.figlet_format(' My 5 ', font='smslant')
    print(colored(title, 'green'))
    strapline = "A Single My 5 Downloader:\n\n"
    print(colored(strapline, 'red'))#
    url = input("Enter video url for download. \n") 
    if 'show' in url: 
        url = url.encode('utf-8', 'ignore').decode().strip()
        main(url)
    else:
        print(f"A correct url has the word 'show' in it.\n \
            Take a URL from the address bar with a video loader.\
                \nYou pasted {url}")
    cleanup()
    exit(0)

if __name__ == "__main__":
    run()
    cleanup()
    exit(0)
    





