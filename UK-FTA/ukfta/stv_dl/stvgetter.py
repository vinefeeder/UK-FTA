# A_n_g_e_l_a
# Revision August 2024

from selectolax.lexbor import LexborHTMLParser
import json, sys, os
import httpx
from httpx import Client
import re, subprocess
import pyfiglet as PF
from termcolor import colored
import time
from beaupy.spinners import *
from rich.console import Console
from pathlib import Path
import glob

# see README.md in top level directory
try:
    import subby        
except:
    pass

# do not change order here
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))
from configs import  config

WVD_PATH = config.WVDPATH
SAVE_PATH = config.SAVEPATH
SAVE_PATH = Path(SAVE_PATH)
try:
    SAVE_PATH.mkdir(exist_ok=True, parents=True)
except:
    print("Error creating save directory. Have you set up your save folder from Config in the menu?")
BATCH_DOWNLOAD = config.BATCH_DOWNLOAD

console = Console()

timeout = httpx.Timeout(10.0, connect=60.0)
client = Client(
        headers={
            'user-agent': 'Dalvik/2.9.8 (Linux; U; Android 9.9.2; ALE-L94 Build/NJHGGF)',
        },
    timeout=timeout,
    )


# global constants
pk = "BCpkADawqM1WJ12PwtUWqGXx3nbAo2XVSxyAQxPRZKBc75svhrUB9qIMPN_d9US0Vib5smumeNMbntSmZIpzeVV1iUrnzYgf5k7UMaVN46PGYe_oSZ-xbPVnsm4"
pkey_drm = "BCpkADawqM1fQNUrQOvg-vTo4VGDTJ_lGjxp2zBSPcXJntYd5csQkjm7hBKviIVgfFoEJLW4_JPPsHUwXNEjZspbr3d1HqGDw2gUqGCBZ_9Y_BF7HJsh2n6PQcpL9b2kdbi103oXvmTNZWiQ"
 

DRM = False

def get_key(pssh: str, lic_url: str , cert_b64=None) -> str:
    
    print("Using pywidevine WVD on this machine")   
    from pywidevine.cdm import Cdm
    from pywidevine.device import Device
    from pywidevine.pssh import PSSH
    pssh = PSSH(pssh)
    device = Device.load(WVD_PATH)
    cdm = Cdm.from_device(device)
    session_id = cdm.open()
    challenge = cdm.get_license_challenge(session_id, pssh)
    licence = httpx.post(lic_url, data=challenge, headers=None)
    licence.raise_for_status()
    cdm.parse_license(session_id, licence.content)
    mykeys = ''
    for key in cdm.get_keys(session_id):
        if key.type=='SIGNING':
            pass
        else:
            print(f"Keys found {key.kid.hex}:{key.key.hex()}")
            mykeys += f"{key.kid.hex}:{key.key.hex()}"
    cdm.close(session_id)
    return mykeys 

def get_initial_data(url):
    headers = {
        'Accept': '*/*',
        'Connection': 'keep-alive',
        'Origin': 'https://player.stv.tv',
        'Referer': 'https://player.stv.tv/',
        }
    response = client.get(url, headers = headers)
    if response.status_code != 200:
        print(f"Error {response.status_code} on {url}")
        exit(0)
    tree = LexborHTMLParser(response.text)
    jsondata = tree.root.css_first('#__NEXT_DATA__').text()

    myjson = json.loads(jsondata)
    test = None
    try:
        test =  myjson['props']['pageProps']['data']['tabs'][0]['data']  # fails on non-drm
    except:
        pass
    if test==None: # not DRM
        pass 
    else:  # Is DRM
        DRM = True
        #print(test)
    try:
        episodeId = str(myjson['props']['pageProps']['episodeId'])
        interim = f"/episodes/{episodeId}"
        jsonshort = myjson['props']['initialReduxState']['playerApiCache'][interim]['results']
        videoId = jsonshort['video']['id']
        guid    = jsonshort['guid']
        try:
            seriesguid = jsonshort['playerSeries']['guid']
        except:
            seriesguid = 'null'
        DRM = jsonshort['programme']['drmEnabled']
    except Exception as e:
        print(e)
        print("The data supplied has an non-compliant structure\nwhich breaks this script.\nUnable to download.")
        exit(0)
    
    return(videoId,seriesguid, guid, DRM)

def get_stage_two_no_drm(videoid):
    client.headers = {
        'Accept': f'application/json;pk={pk}',
    }
    url = f"https://edge.api.brightcove.com/playback/v1/accounts/1486976045/videos/{videoid}"
    response = client.get(url)
    if response.status_code != 200:
        print(f"Error {response.status_code} on {url}")
        exit(0)
    myjson = json.loads(response.text)
    #console.print_json(data=myjson) 
    videoname = myjson['name']
    manifest = myjson['sources'][0]['src'] 
    folder = myjson['tags'][0]


    return videoname, manifest, folder

def get_stage_two_drm(videoid):
    client.headers = {
        'Accept': f'application/json;pk={pkey_drm}',
    }
    url = f"https://edge.api.brightcove.com/playback/v1/accounts/6204867266001/videos/{videoid}"
    response = client.get(url)
    if response.status_code != 200:
        print(f"Error {response.status_code} on {url}")
        exit(0)
    myjson = json.loads(response.text)
    videoname = myjson['name'].replace(' ','_').replace("'",'')
    manifest = myjson['sources'][3]['src']
    license = myjson['sources'][3]['key_systems']['com.widevine.alpha']['license_url']
    folder = myjson['tags'][0]
    response = client.get(manifest)
    if response.status_code != 200:
        print(f"Error {response.status_code} on {manifest}")
        exit(0)
    manifest_text = response.text
    m = re.search('<cenc:pssh>(AAAA.+?)</cenc:pssh>', manifest_text) 
    if m:
        pssh = m.group(1)
    keys = get_key(pssh, license, None)
    return(keys, manifest, videoname, folder)

# add leading zero to series or episode
def pad_number(match):
    number = int(match.group(1))
    return format(number, "02d")

def clean_videoname(videoname):
    illegals = "*'%$!(),.:;"
    replacements = {
        'Episode ': 'E',
        'Series ': 'S',
        ' - ': ' ',
        ' ': '_',
        '&': 'and',
        '?': '',
    }

    videoname = ''.join(c for c in videoname if c.isprintable() and c not in illegals)
    # standardize and compact videoname    
    for rep in replacements:  
        videoname = videoname.replace(rep, replacements[rep])
    videoname = re.sub(r"(\d+)", pad_number, videoname).lstrip('_').rstrip('_')
    result = re.search(r"(^.*S\d+)_(E\d*.*)", videoname)
    try:
        pre = result.group(1)
        post = result.group(2)
        post = re.sub(r"(_of_\d{2})",  '', post)
        videoname = pre+post
    except:
        pass
    videoname = splitter(videoname, '_')
    videoname = refactor(videoname)
    
    return videoname

def refactor(videoname):
    #print("Refactoring videoname....")
    try:
        string = videoname
        pattern = r'S\d{2}E\d{2}'
        match = re.search(pattern, string)
        if match:
            start = match.start()
            end = match.end() 
            suffix = '[' + string[end:] + ']'
            matched_part = string[start:end]
            result = f"{string[:start]}{suffix}_{matched_part}"
            return result.replace('_[_', '_[')
        else:
            return videoname
    except:  
        return videoname
    
def convertsubtitles(pathin: str):
    # tries to use subby see:- https://github.com/vevv/subby
    # or falls back to ffmpeg if subby is not installed
    # ffmpeg lacks error correction for oddly formatted vtt files.

    SUBTITLES = True
    pathout = f"./subs.en.srt"
    pathin = Path(pathin)
    pathout = Path(pathout)
    my_file = Path("./subs.en.vtt")
    
    if my_file.is_file():
        try:
            subprocess.run(['subby', 'convert', f'{pathin}']) 
        except:
            subprocess.run(['ffmpeg', '-loglevel', 'quiet',  '-hide_banner', '-y', '-i', f'{pathin}' , f'{pathout}'])  # overwrite existing outpath
    else:
        SUBTITLES = False
    return SUBTITLES


def get_stage_one_data(videoid, seriesguid, guid, DRM ):

    ############################# may need editing  #############################
    m3u8dl = "N_m3u8DL-RE" 
    ############################ end may need editing  ##########################

    def downloaddrm(manifest, videoname, folder, keys, HASSUBS=False):
        command = ([
        m3u8dl,
            manifest,
            '-sa',
            'best',
            '-sv',
            'best',
            '--save-name',
            videoname,
            '--save-dir',
            f'{SAVE_PATH}/STV/{folder}',
            '--tmp-dir',
            './',
            '-mt',
            '--key',
            keys,
            '-M',
            'format=mkv:muxer=mkvmerge',
            
        ]) 
        if HASSUBS:
            command.extend([
                "--mux-import:path=./subs.en.srt:lang=eng:name='Eng'",
                '--no-log'
            ])
        cleaned_command = [cmd.replace('\n', ' ').strip() for cmd in command]
        return cleaned_command
   
    def downloadnodrm(manifest, videoname, folder, HASSUBS=False):
        command = ([
        m3u8dl,
            manifest,
            '-sa',
            'best',
            '-sv',
            'best',
            '--save-name',
            videoname,
            '--save-dir',
            f'{SAVE_PATH}/STV/{folder}',
            '--tmp-dir',
            './',
            '-mt',
            '-M',
            'format=mkv:muxer=mkvmerge'
            ]) 

        if HASSUBS:
            command.extend([
                "--mux-import:path=./subs.en.srt:lang=eng:name='Eng'",
                '--no-log'
            ])
        cleaned_command = [cmd.replace('\n', ' ').strip() for cmd in command]
        return cleaned_command
    
    
    if DRM:
        headers = {
        'Accept': '*/*',
        'Connection': 'keep-alive',
        'Origin': 'https://player.stv.tv',
        'Referer': 'https://player.stv.tv/',
        'Stv-Drm': 'true',
        }
        url = f"https://player.api.stv.tv/v1/episodes/{guid}?groupToken=0071"
    elif seriesguid == 'null':
        headers = {
        'Accept': '*/*',
        'Connection': 'keep-alive',
        'Origin': 'https://player.stv.tv',
        'Referer': 'https://player.stv.tv/',
        }
        url = f"https://player.api.stv.tv/v1/episodes/{guid}?groupToken=0071"    
    else:
        headers = {
        'Accept': '*/*',
        'Connection': 'keep-alive',
        'Origin': 'https://player.stv.tv',
        'Referer': 'https://player.stv.tv/',
        }
        url = f"https://player.api.stv.tv/v1/episodes?series.guid={seriesguid}"
    
    response = client.get(url , headers = headers) 
    if response.status_code != 200:
        print(f"Error {response.status_code} on {url}")
        exit(0)   
    myjson = json.loads(response.text)
    mylist = myjson['results'] 
    
    if DRM:
        videoid = mylist['video']['id']
        keys, manifest, videoname, folder = get_stage_two_drm(videoid)
    else:
        videoname, manifest, folder = get_stage_two_no_drm(videoid)
    folder = folder.replace('vp-','').title()
    videoname = clean_videoname(videoname).replace('_[]_','_')

    # try subtitles
    try:
        subprocess.run([m3u8dl, manifest,  '-ss' ,  'name="English":for=all', '--sub-format:VTT', '--save-name', 'subs', '--save-dir', './'])
        HASSUBS = convertsubtitles(f"./subs.en.vtt")
    except Exception as e:
        print(e)
  
    if DRM:    
        command = downloaddrm(manifest, videoname, folder, keys, HASSUBS)          
    else:  
        command = downloadnodrm(manifest, videoname, folder, HASSUBS)

    if BATCH_DOWNLOAD:
        with open(f'{SAVE_PATH}/batch.txt', 'a') as f:
            f.write(' '.join(command) + '\n')
    else:
        subprocess.run(command)

    #clear existing subs
    for f in glob.glob("./*vtt"):
        os.remove(f)
        
    for f in glob.glob("./subs.en.srt"):
        os.remove(f)

    print(f"[info] {videoname}.mkv is in {SAVE_PATH}/STV/{folder}")


def cleanup():

    #############################################################################################
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

def entrypoint(url):
    print("[info] Preparing to download ...")
    videoid, seriesguid,guid, DRM = get_initial_data(url) 
    get_stage_one_data(videoid, seriesguid, guid, DRM)
    return        

def run():
    title = PF.figlet_format(' S T V ', font='smslant')
    print(colored(title, 'green'))
    print()
    strapline = "An STV Video Search, Selector and Downloader.\n\n"
    print(colored(strapline, 'red'))
    print("\n\nCorrect urls look like this:-\nhttps://player.stv.tv/episode/4hml/the-tower")
    while True:
        url = input("Address Bar url? ")
        url = url.encode('utf-8', 'ignore').decode().strip()
        if not url.__contains__('episode'):
            print("\nThe word 'episode' SHOULD be in the url. \nTry again.\n")
        else:
            break
    # get_initial
    videoid, seriesguid,guid, DRM = get_initial_data(url)
    get_stage_one_data(videoid, seriesguid, guid, DRM) 
    cleanup()
    exit(0)
    
def splitter(test_str, splt_char):
    # Identifies and removes repeat strings in videonames
    # Split string on Kth Occurrence of Character
    # Using split() + join()
    
    K = test_str.count(splt_char) # find index of mid char
    print(K)
    if K % 2 == 0: # is even, so no mid-string
        return test_str
    else:
        K = int((K+1)/2)
  
    temp = test_str.split(splt_char)
    res = splt_char.join(temp[:K]), splt_char.join(temp[K:])
    if str(res[0]) == str(res[1]):
        return res[0]
    else:
        return test_str

if __name__ == '__main__':
    run()