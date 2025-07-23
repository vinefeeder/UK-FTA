# A_n_g_e_l_a  20:09:2023 
# Reworked June 2025 to 1080p

# script to download videos from direct URL entry.
# Called as the downloader from itv_loader.py

# uses pywidevine 
# folder structures are created of the form ./output/ITV/'series-title'/'videos name'


import re
import subprocess
from base64 import b64encode
from pathlib import Path
import httpx
from httpx import  Client
from selectolax.lexbor import LexborHTMLParser
from beaupy.spinners import *
import os
from termcolor import colored
import pyfiglet as PF
import json
import jmespath
import sys
import os, glob
from rich.console import Console
from scrapy import Selector
import time


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))
from configs import  config


WVD_PATH = config.WVDPATH
SAVE_PATH = Path(config.SAVEPATH)
BATCH_DOWNLOAD = config.BATCH_DOWNLOAD
SAVE_PATH.mkdir(exist_ok=True, parents=True)

SUBS = False

console = Console()

class ITV:
    def __init__(self):
        timeout = httpx.Timeout(10.0, connect=60.0)
        self.client = Client(
            headers={
                "User-Agent": "okhttp/4.9.3",
                "Accept-Language": "en-US,en;q=0.8",
                "Origin": "https://www.itv.com",
                "Connection": "keep-alive",
            },
        timeout=timeout,
        )
        self.cookies = httpx.Cookies()
        return
    
    def rinse(self,string):
        illegals = "*'%$!(),.;"  # safe for urls
        string = ''.join(c for c in string if c.isprintable() and c not in illegals)
        replacements = {
            '"': '',
            ' ': '_',
            '_-_': '_',
            '&': 'and',
            ':': '',
            '_Content': '',
        }
        for rep in replacements:  
            string = string.replace(rep, replacements[rep])
        string = re.sub(r'(S\d{1,2})(_)(E\d{1,2})', r'\1\3', string) #selective remove underscore
        return string
    
    def get_pssh(self, mpd_url: str) -> str:
        r = self.client.get(mpd_url)
        r.raise_for_status()
        kid = (
            LexborHTMLParser(r.text)
            .css_first('ContentProtection')
            .attributes.get('cenc:default_kid')
            .replace('-', '')
        )
        s = f'000000387073736800000000edef8ba979d64acea3c827dcd51d21ed000000181210{kid}48e3dc959b06'
        return b64encode(bytes.fromhex(s)).decode()
    
    
    def get_key(self, pssh, license_url):

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
        for key in cdm.get_keys(session_id):
            if key.type == 'CONTENT':
                keys.append(f"{key.kid.hex}:{key.key.hex()}")

        cdm.close(session_id)

        return ":".join(keys)
        
    def download(self, url: str, index: int | str) -> None:
        if type(index)==int:
            INDEX=True
        else:
            INDEX=False
    
        title, extendtitle, data = self.get_data(url)

        compositetitle = title+' '+extendtitle
        video = data['Playlist']['Video']
        media = video['MediaFiles']
        illegals = "*'%$!(),.:;"
        replacements = {
            'ITV01': 'ITV1',
            'ITV02': 'ITV2',
            'ITV03': 'ITV3',
            'ITV04': 'ITV4',
            'SNone': 'S00',
            'Sothers': 'S00',
            'ENone': '_Special',
            '  Episode ': 'E',
            '  Series ': '_S',
            'otherepisodes': '_extra',
            'ITVX': '',
            ' ': '_',
            '&': 'and',
            '?': '',
        }

        # sanitize videoname
        videoname = ''.join(c for c in compositetitle if c.isprintable() and c not in illegals)
        # and compact    
        videoname = re.sub(r"(\d+)", pad_number, videoname).lstrip('_').rstrip('_') 
        for rep in replacements:  
            videoname = videoname.replace(rep, replacements[rep])      
        try:
            folder = title
            folder = self.rinse(folder)
        except:
            folder = 'specials'
        myvideoname = self.rinse(videoname)

        try:
            subs_url = video['Subtitles'][0]['Href']
            subs = self.client.get(subs_url)
            if subs.status_code==200:
                SUBS = True
                f = open(f"{myvideoname}.subs.vtt", "wb") # bytes needed for N_m's subtitles
                subtitles = subs.content
                f.write(subtitles)
                f.close()
                os.system(f"ffmpeg -loglevel quiet -hide_banner -i ./{myvideoname}.subs.vtt  ./{myvideoname}.subs.srt")
            else:
                SUBS=False
        except:
            SUBS = False  

        mpd_url = video['MediaFiles'][0]['Href']
        lic_url = video['MediaFiles'][0]['KeyServiceUrl']

        pssh = self.get_pssh(mpd_url)
        key = self.get_key(pssh, lic_url)

        if SUBS: 
            subs = f"--mux-import:path=./{myvideoname}.subs.srt:lang=eng:name='English'"
        else:
            subs = '--no-log'
        if BATCH_DOWNLOAD:
            subs = '--no-log'

        OUT_PATH = Path(f'{SAVE_PATH}/ITV/{folder}')
        OUT_PATH.mkdir(exist_ok=True, parents=True)
        out_path = str(OUT_PATH)
        if INDEX:
            myvideoname = f"{index}.{myvideoname}"
        m3u8dl = 'N_m3u8DL-RE'
        command = [
            m3u8dl,
            mpd_url,
            '--append-url-params',
            '--auto-select',
            '--save-name',
            myvideoname,
            '--save-dir',
            out_path,
            '--tmp-dir',
            './',
            '-mt',
            '--key',
            key,
            '-M',
            'format=mkv:muxer=mkvmerge',
            subs, 
        ]
        cleaned_command = [cmd.replace('\n', ' ').strip() for cmd in command]

        if BATCH_DOWNLOAD:
            with open(f'{SAVE_PATH}/batch.txt', 'a') as f:
                f.write(' '.join(cleaned_command) + '\n')
        else:
            #print(command)
            subprocess.run(command)
            print(f"File saved to {OUT_PATH}/{title}")
        
        print(f"[info] {myvideoname}.mkv is in {OUT_PATH}")
        if SUBS:
            for f in glob.glob("*.vtt"):
                os.remove(f)
            for f in glob.glob("*.srt"):
                os.remove(f)
    
    def get_data(self, url: str) -> tuple:
        spinner = Spinner(DOTS)
        spinner.start()
        headers={

        'Referer': 'https://www.itv.com/',
        }
        # Films seem to have some sort protection in that normal data rules do not apply
        # So we need to do some extra work to get the data
        if url.count('/') == 6:
            pass
        else:
            initresp = self.client.get(url, headers=headers, follow_redirects=True)
            if initresp.status_code == 200:
                sel = Selector(text = initresp.text)
                selected = sel.xpath('//*[@id="__NEXT_DATA__"]').extract()
                selected = selected[0]
                pattern = r'\s*({.*})\s*' 
                myjson = json.loads(re.search(pattern, selected).group())
                #console.print_json(data=myjson) # for dev
                episodeId = myjson['props']['pageProps']['seriesList'][0]['titles'][0]['encodedEpisodeId']['letterA']
                
                myjson =myjson['query']
                res = jmespath.search("""
                    {
                    programmeSlug: programmeSlug
                    programmeId: programmeId 
                    }""", myjson
                )
            url =f"https://www.itv.com/watch/{res['programmeSlug']}/{res['programmeId']}/{episodeId}"    
        r = self.client.get(url,  follow_redirects=True)
        mycookies = self.client.cookies.jar
        self.cookie_header_value = "; ".join([f"{c.name}={c.value}" for c in mycookies])

    
        if r.status_code == 200:
            sel = Selector(text = r.text)
            selected = sel.xpath('//*[@id="__NEXT_DATA__"]').extract()
            selected = selected[0] 
            pattern = r'\s*({.*})\s*' 
            myjson = json.loads(re.search(pattern, selected).group())
            myjson =myjson['props']['pageProps']
            #console.print_json(data=myjson) # for dev
            try:
                res = jmespath.search("""
                    episode.{
                    episode: episode
                    eptitle: episodeTitle
                    series: series            
                    description: description
                    channel: channel
                    content: contentInfo                         
                    } """,  myjson)

                
                title = jmespath.search("programme.title", myjson)
                title = title
                episode = res['episode']
                episodetitle = res['eptitle']
                series = res['series']
                channel = res['channel']
            except:
                print("No episode data found in the json")
                print("Try again; use the URL with a Greedy Search. \nSome Film Titles need a full workout to download successfully")
                exit(1)
            if episodetitle==None:
                temp = res['content']
                if re.match(r"S\d{1,2}..E\d{1,2}", temp):
                    temp = res['description']
                    temp = temp.split()[:6] # take first 6 words for episodetitle
                episodetitle = temp
            if title in episodetitle:
                episodetitle = ''
            extendtitle = f"{episodetitle}_{channel}_S{series}E{episode}"
            magni_url = jmespath.search('[ seriesList.[*].titles.[*].playlistUrl , episode.playlistUrl]', myjson)
            magni_url = (next (item for item in magni_url if item is not None))
            
            payload =   {
                        "client": {
                            "id": "lg"
                        },
                        "device": {
                            "deviceGroup": "ctv"
                        },
                        "variantAvailability": {
                            "player": "dash",
                            "featureset": [
                            "mpeg-dash",
                            "widevine",
                            "outband-webvtt",
                            "hd",
                            "single-track"
                            ],
                            "platformTag": "ctv",
                            "drm": {
                            "system": "widevine",
                            "maxSupported": "L3"
                            }
                        }
                        }
            payload = json.dumps(payload)
   
            headers = {
            "Accept": "application/vnd.itv.vod.playlist.v4+json",
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            "Accept-Language": "en-US,en;q=0.9,da;q=0.8",
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "Content-Length": str(len(payload)),
            "Cookie": self.cookie_header_value,
            'Host':'magni.itv.com',
            'User-Agent': 'okhttp/4.9.3',
            }
           
            r = self.client.post(magni_url, headers=headers, content=payload)

            #console.print_json(data=r.json())
            spinner.stop()
            return title, extendtitle, r.json()
        else:
            print(f"The response code {r.status_code} did not indicate successs!")
            print(f"The web page content returned was:-\n\n {r.content}\n\nExiting!")
            print(f"Be sure to copy a page url for a playable video ")
            exit(1)
            
    def run(self) -> int: 
        while True:
            url = input("Enter video url for download. \n") 
            if 'watch'in url.lower():
                break
            else:
                print("A correct download url has 'watch/<video-title>/<alpha-numeric>' in the line.") 
                continue  
        self.download(url, 'No')
        return 0

def pad_number( match):
    number = int(match.group(1))
    return format(number, "02d")

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


if __name__ == "__main__":
    title = PF.figlet_format(' I T V X ', font='smslant')
    print(colored(title, 'green'))
    strapline = "A Single ITVX Downloader:\n\n"
    print(colored(strapline, 'red'))
    print()
    myITV = ITV()
    myITV.run()
    cleanup()
    exit(0)

