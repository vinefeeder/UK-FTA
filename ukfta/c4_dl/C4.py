
    # A_n_g_e_l_a  01:10:2023
# revised data 02@02:2024


import base64
from base64 import b64encode
import json
import os, sys
import re
import subprocess
from bs4 import BeautifulSoup
import subprocess
import pyfiglet as PF
from termcolor import colored
from pathlib import Path
from beaupy.spinners import *
from httpx import Client
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from pywidevine.pssh import PSSH
from pywidevine.device import Device
from pywidevine.cdm import Cdm
import time
from beaupy.spinners import *
from rich.console import Console
from rich.prompt import Prompt
import requests
import glob

console = Console()

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))
from configs import  config
import shutil

WVD_PATH = config.WVDPATH
SAVE_PATH = config.SAVEPATH
C4_USES_N_m3u8DLRE = config.C4_USES_N_m3u8DLRE
BATCH_DOWNLOAD = config.BATCH_DOWNLOAD

# this uses pywidevine system library and not WKS-KEYS so run it away from WKS-KEYS
# Create a WideVine Descriptor (wvd) file in folder WVD; Navigate to where you key and blob are
# 'mkdir WVD' then
# 'pywidevine create-device -k device_private_key -c device_client_id_blob -t "ANDROID" -l 3 -o WVD'

# 
# This software optionally uses shaka-packager to decrypt files see https://github.com/shaka-project/shaka-packager/releases
# rename the packager binary to shaka-packager and put it in your system PATH
# see line 343 (or there-abouts)  '--use-shaka-packager', 


#
# link for https://github.com/nilaoda/N_m3u8DL-RE/releases
n_m3u8dl = "N_m3u8DL-RE"            # change to however it is named

DOWNLOAD_DIR = SAVE_PATH
DOWNLOAD_DIR = Path(DOWNLOAD_DIR)
try:
    DOWNLOAD_DIR.mkdir(exist_ok=True, parents=True)
except:
    print("Error creating directory to save files. Have you set up your save folder from Config in the menu?")


TMP_DIR = Path('./tmp/')  # relative or full path


TMP_DIR.mkdir(exist_ok=True, parents=True)

DEFAULT_HEADERS = {
    'Content-type': 'application/json',
    'Accept': '*/*',
    'Referer': 'https://www.channel4.com/',
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 12; SM-G930F Build/SQ1D.220105.007)"
}

MPD_HEADERS = {
    'Content-type': 'application/dash+xml',
    'Accept': '*/*',
    'Origin': "ak-jos-c4assets-com.akamaized.net",
    'Referer': 'https://www.channel4.com/',
    "user-agent": "Dalvik/2.1.0 (Linux; U; Android 12; SM-G930F Build/SQ1D.220105.007)"
}


global client
client = Client()

class ComplexJsonEncoder(json.JSONEncoder):
    def default(self, o):
        if hasattr(o, 'to_json'):
            return o.to_json()
        return json.JSONEncoder.default(self, o)


class Video:
    def __init__(self, video_type: str, url: str):
        self.video_type = video_type
        self.url = url

    def to_json(self):
        resp = {}

        if self.video_type != "":
            resp['type'] = self.video_type
        if self.url != "":
            resp['url'] = self.url
        return resp


class DrmToday:
    def __init__(self, request_id: str, token: str, video: Video, message: str):
        self.request_id = request_id
        self.token = token
        self.video = video
        self.message = message

    def to_json(self):
        resp = {}

        if self.request_id != "":
            resp['request_id'] = self.request_id
        if self.token != "":
            resp['token'] = self.token
        if self.video != "":
            resp['video'] = self.video
        if self.message != "":
            resp['message'] = self.message
        return resp


class Status:
    def __init__(self, success: bool, status_type: str):
        self.success = success
        self.status_type = status_type


class VodConfig:
    def __init__(self, vodbs_url: str, drm_today: DrmToday, message: str):
        self.vodbs_url = vodbs_url
        self.drm_today = drm_today
        self.message = message


class VodStream:
    def __init__(self, token: str, uri: str, brand_title: str, episode_title: str):
        self.token = token
        self.uri = uri
        self.brand_title = brand_title
        self.episode_title = episode_title

    def to_json(self):
        resp = {}

        if self.token != "":
            resp['token'] = self.token
        if self.uri != "":
            resp['uri'] = self.uri
        return resp


class LicenseResponse:
    def __init__(self, license_response: str, status: Status):
        self.license_response = license_response
        self.status = status

    def to_json(self):
        resp = {}

        if self.license_response != "":
            resp['license'] = self.license_response
        if self.status != "":
            resp['status'] = self.status
        return resp


def decrypt_token(token: str):
    try:
        cipher = AES.new(
            b"\x41\x59\x44\x49\x44\x38\x53\x44\x46\x42\x50\x34\x4d\x38\x44\x48",
            AES.MODE_CBC,
            b"\x31\x44\x43\x44\x30\x33\x38\x33\x44\x4b\x44\x46\x53\x4c\x38\x32"
        )
        decoded_token = base64.b64decode(token)
        decrypted_string = unpad(cipher.decrypt(
            decoded_token), 16, style='pkcs7').decode('UTF-8')
        license_info = decrypted_string.split('|')
        return VodStream(license_info[1], license_info[0], '', '')
    except: 
        print('[!] Failed decrypting VOD stream !!!')
        raise


def get_vod_stream(target: str):
    try:
        ## do login
        urla = "https://api.channel4.com/online/v2/auth/token"
        headers1 = {
        "accept-encoding": "gzip",
        "connection": "Keep-Alive",
        "content-length": "103",
        "content-type": "application/x-www-form-urlencoded",
        "host": "api.channel4.com",
        "user-agent": "Dalvik/2.1.0 (Linux; U; Android 14; Pixel 6a Build/UQ1A.240205.002) C4oD_Android/9.7.2 (uid:824f075b-dc9a-4dea-b059-6d6c040376ac; tid:-; did:Google_Pixel 6a_34;)",
        "x-correlation-id":"ANDROID-cb8d7eb8-5494-4792-92a6-353e33a30fd0",
        }

        data1 =(
        "grant_type=client_credentials&client_id=36UUCt98VMQvBAgQ27Au8zGHl31N9LQ1&client_secret=JYswyHvGe62VlikW"
        )
        response1 = requests.post(url=urla, headers=headers1, data=data1).json()
        bearertoken = response1["accessToken"]
        
        url = "https://api.channel4.com/online/v1/vod/stream/"+target+"?client=android-mod"

        headers = {
            'accept-encoding': 'gzip',
            'authorization': 'Bearer '+ bearertoken,
            'connection': 'Keep-Alive',
            'host': 'api.channel4.com',
            'x-c4-app-version': '"android_app:9.7.2"',
            'x-c4-date': '2024-03-02T11:10:28Z',
            'x-c4-device-name': 'Google Pixel 6a (bluejay)',
            'x-c4-device-type': 'mobile',
            'x-c4-optimizely-datafile': 'unknown',
            'x-c4-platform-name': 'android',
        }

        ## end do login
        
        myjson = client.get(url, headers=headers).json()
        #console.print_json(data=myjson)
        uri = myjson['videoProfiles'][0]['streams'][0]['uri']
        token = myjson['videoProfiles'][0]['streams'][0]['token']
        brand_title = myjson['brandTitle']
        brand_title = brand_title.replace(':', ' ').replace('/', ' ')
        episode_title = myjson['episodeTitle']
        episode_title = episode_title.replace('/', ' ').replace(':', ' ')
        vod_stream = VodStream(token, uri, brand_title, episode_title)
        return vod_stream
    except: 
        print('[!] Failed getting VOD stream !!!')
        raise


def get_asset_id(url: str):
    try:
        req = client.get(url)

        init_data = re.search(
            r'<script>window\.__PARAMS__ = (.*)</script>',
            ''.join(
                req.content.decode()
                .replace('\u200c', '')
                .replace('\r\n', '')
                .replace('undefined', 'null')
            )
        )
        init_data = json.loads(init_data.group(1))
        asset_id = int(init_data['initialData']['selectedEpisode']['assetId'])

        if asset_id == 0:
            raise  
        return asset_id
    except:  
        print('[!] Failed getting asset ID !!!')
        raise


def get_config():
    try:
        req = client.get(
            'https://static.c4assets.com/all4-player/latest/bundle.app.js')
        #req.raise_for_status
        configs = re.findall(
            r"JSON\.parse\(\'(.*?)\'\)",
            ''.join(
                req.content.decode()
                .replace('\u200c', '')
                .replace('\\"', '\"')
            )
        )
        config = json.loads(configs[1])
        #console.print_json(data = config)
        video_type = config['protectionData']['com.widevine.alpha']['drmtoday']['video']['type']
        message = config['protectionData']['com.widevine.alpha']['drmtoday']['message']
        video = Video(video_type, '')
        drm_today = DrmToday('', '', video, message)
        vod_config = VodConfig(config['vodbsUrl'], drm_today, '')
        return vod_config
    except: 
        print('[!] Failed getting production config !!!')
        raise


def get_service_certificate(url: str, drm_today: DrmToday):
    try:
        req = client.post(url, data=json.dumps(
            drm_today.to_json(), cls=ComplexJsonEncoder), headers=DEFAULT_HEADERS)
        req.raise_for_status
        resp = json.loads(req.content)
        license_response = resp['license']
        status = Status(resp['status']['success'], resp['status']['type'])
        return LicenseResponse(license_response, status)
    except:
        print('[!] Failed getting signed DRM certificate !!!')
        raise


def get_license_response(url: str, drm_today: DrmToday):
    try:
        req = client.post(url, data=json.dumps(
            drm_today.to_json(), cls=ComplexJsonEncoder), headers=DEFAULT_HEADERS)
        req.raise_for_status
        resp = json.loads(req.content)
        license_response = resp['license']
        status = Status(resp['status']['success'], resp['status']['type'])

        if not status.success:
            raise 
        return LicenseResponse(license_response, status)
    except:  
        print('[!] Failed getting license challenge !!!')
        raise


def get_kid(url: str):
    try:
        req = client.get(url, headers=MPD_HEADERS)
        #req.raise_for_status
        kid = re.search('cenc:default_KID="(.*)"', req.text).group(1)
        return kid
    except:  
        print('[!] Failed getting KID !!!')
        raise


def generate_pssh(kid: str):
    try:
        kid = kid.replace('-','')
        s = f'000000387073736800000000edef8ba979d64acea3c827dcd51d21ed000000181210{kid}48e3dc959b06'
        return b64encode(bytes.fromhex(s)).decode()
    except: 
            print('[!] Failed generating PSSH !!!')
            raise

def get_videoname_by_soup(url):
  
    HEADERS = {"user-agent": "Dalvik/2.1.0 (Linux; U; Android 12; SM-G930F Build/SQ1D.220105.007)\
            C4oD_Android/9.4.3 (uid:3e113df8-0a46-4fa6-8e5f-ee0b3d5f0a3b; tid:-; did:samsung_SM-G930F_31;)",
            'Accept-Language': 'en-US, en;q=0.5'}
  
    webpage = client.get(url, headers=HEADERS)
    soup = BeautifulSoup(webpage.content, "html.parser")
    videoname = str(soup.text).split('|')[0].replace(':','').replace("'",'').replace('-','').replace(' ','_')
    videoname = re.sub(r"(\d+)", pad_number, videoname)
    videoname = videoname.replace('Watch_','').replace('_Series_', 'S').replace('_Episode_','E').rstrip('_')
    return videoname


# add leading zero to series or episode
def pad_number(match):
    number = int(match.group(1))
    return format(number, "02d")

def check_file(file_name, file_size = 300):
    
    # Check if the file exists and if its size is at least 300 bytes
    if os.path.isfile(file_name) and os.path.getsize(file_name) >= file_size:
        return True
    else:
        return False


def get_streams(mpd, decryption_key, output_title, brand_title): 
    SUBS = False
    brand_title = brand_title
    brand_title = clean(brand_title) 
    output_title = clean(output_title)
    # check subs download a valid file
    # and merge subs if file is good.
    subs_command = ([
        n_m3u8dl,
        mpd,
        '--sub-only',
        'True',
        "-ss",
        "id='0'", 
        '--save-name',
        'subs' ,
        '--tmp-dir',
        TMP_DIR,
    ])
    try:   
        subprocess.run(subs_command)
        SUBS = check_file('subs.srt')  # check if file exists and is over 300 bytes    
    except:
        pass
    
    if SUBS:
        command = ([
            n_m3u8dl,
                mpd,
                #'--auto-select',
                '-sa',
                'all',
                '-sv',
                'best',
                '--save-name',
                output_title,
                '--save-dir',
                f'{DOWNLOAD_DIR}/C4/{brand_title}/',
                '--tmp-dir',
                TMP_DIR,
                #'--use-shaka-packager',
                #'--decryption-binary-path',  # windows users: uncomment this and next. Edit next path
                #'./shaka-packager.exe',
                '--key',
                decryption_key,
                '-mt',
                "--mux-import:path=./subs.srt:lang=eng:name='Eng'",
                '-M',
                'format=mkv:muxer=mkvmerge',
                '--no-log', 
                ]) 
    else:
         command = ([
            n_m3u8dl,
                mpd,
                #'--auto-select',
                '-sa',
                'all',
                '-sv',
                'best', 
                '-ds',
                'id="0"',
                '--save-name',
                output_title,
                '--save-dir',
                f'{DOWNLOAD_DIR}/C4/{brand_title}/',
                '--tmp-dir',
                TMP_DIR,
                #'--use-shaka-packager',
                #'--decryption-binary-path',  # windows users: uncomment this and next. Edit next path
                #'./shaka-packager.exe',
                '--key',
                decryption_key,
                '-mt',
                '-M',
                'format=mkv:muxer=mkvmerge',
                '--no-log', 
                ]) 
         
    cleaned_command = [str(cmd).replace('\n', ' ').strip() for cmd in command]


    if BATCH_DOWNLOAD:
        with open(f'{SAVE_PATH}/batch.txt', 'a') as f:
            f.write(' '.join(cleaned_command) + '\n')
    else:
        # print(command)
        subprocess.run(command)
        print(f"File saved to {DOWNLOAD_DIR}/{brand_title}")
        for f in glob.glob("./subs.srt"):
            os.remove(f)
    return

### alternate downloader
def get_streams_by_ytdlp(mpd, decryption_key, output_title, brand_title): 
    brand_title = brand_title
    brand_title = clean(brand_title) 
    output_title = clean(output_title)
    # change order
    
    yt_dlp = 'yt-dlp'  
    command = ([
            yt_dlp,
            "--allow-u",
            "-q",
            "--no-warnings",
            "--progress",
            "-f",
            "bv,ba", 
            mpd,
            '--write-subs',
            '--convert-subs',
            'srt',
            "-o",
            f"{TMP_DIR}/encrypted{output_title}.%(ext)s"
            ]) 
     
    subprocess.run(command, check = True, )
    bit = decryption_key.split(':')
    key_id = bit[0]
    key = bit[1]
    

    os.system(f'shaka-packager -quiet in={TMP_DIR}/encrypted{output_title}.mp4,stream=video,output_format=mp4,output={TMP_DIR}/{output_title}.mp4  --enable_raw_key_decryption --keys key_id={key_id}:key={key}')
    os.system(f'shaka-packager -quiet in={TMP_DIR}/encrypted{output_title}.m4a,stream=audio,output={TMP_DIR}/{output_title}.m4a --enable_raw_key_decryption --keys key_id={key_id}:key={key}')
   
    command = ([
        'mkvmerge',
        '-q',
        #'-d',
        f'{TMP_DIR}/{output_title}.mp4',
        #'-a',
        f'{TMP_DIR}/{output_title}.m4a',
        #'-s',
        f'{TMP_DIR}/encrypted{output_title}.und.srt',
        '-o',
        f'{DOWNLOAD_DIR}/C4/{brand_title}/{output_title}.mkv',
    ])
    subprocess.run(command,  stderr=subprocess.STDOUT)
    shutil.rmtree(TMP_DIR)
    return


def clean(videoname):
    illegals = "*'%$!(),.:;"
    replacements = {
        'Episode ': 'E',
        'Series ': 'S',
        ' - ': ' ',
        ' ': '_',
        '&': 'and',
        '?': '',
        '!': '',
        '[': '',
        ']': '',
        '(': '',
        ')': '',
        '|': '',
        '~': '',
        '^': '',
        '+': '',
        '=': '',
        '`': '',
        '\\': '',
        '/': '',
        '"': '',
        '\'': '',
        '<': '',
        '>': '',
        '*': '',
        '#': '',
        '$': '',
    }

    videoname = ''.join(c for c in videoname if c.isprintable() and c not in illegals)
    # standardize and compact videoname    
    for rep in replacements:  
        videoname = videoname.replace(rep, replacements[rep])
    return videoname

def main(url ):
    wvd = WVD_PATH

    config = get_config()

    spinner = Spinner(DOTS)
    spinner.start()

    asset_id = get_asset_id(url)
    target = url.split('/')[-1]
    encrypted_vod_stream = get_vod_stream(target)
    # Decrypt the stream token
    decrypted_vod_stream = decrypt_token(encrypted_vod_stream.token)
    # Setup the initial license request
    #mpd
    config.drm_today.video.url = encrypted_vod_stream.uri  # MPD
    # license 'message;
    config.drm_today.token = decrypted_vod_stream.token  # Decrypted Token
    config.drm_today.request_id = asset_id  # Video asset ID
    # Get the SignedDrmCertificate (common privacy cert)
    # sending token lic_url to method
    service_cert = get_service_certificate(
        decrypted_vod_stream.uri, config.drm_today).license_response
    # Load the WVD and generate a session ID
    device = Device.load(wvd)
    cdm = Cdm.from_device(device)
    session_id = cdm.open()
    cdm.set_service_certificate(session_id, service_cert)
    kid = get_kid(config.drm_today.video.url)
    # Generate the PSSH
    pssh = generate_pssh(kid)
    challenge = cdm.get_license_challenge(
        session_id, PSSH(pssh), privacy_mode=True)
    config.drm_today.message = base64.b64encode(challenge).decode('UTF-8')
    # Get license response
    license_response = get_license_response(
        decrypted_vod_stream.uri, config.drm_today)
    # Parse license challenge
    cdm.parse_license(session_id, license_response.license_response)
    terminal_size = os.get_terminal_size().columns
    print('*' * terminal_size)
    print(f'[  URL  ] {url}')
    decryption_key = ''
    # Return keys
    for key in cdm.get_keys(session_id):
        if key.type == 'CONTENT':
            decryption_key = f'{key.kid.hex}:{key.key.hex()}'
            print(f'[ KEY ] {key.kid.hex}:{key.key.hex()}')
    print(f'[  MPD  ] {config.drm_today.video.url}')
    print('*' * terminal_size)
    # Close session, disposes of session data
    cdm.close(session_id)

    videoname = get_videoname_by_soup(url)
    ep_title = encrypted_vod_stream.episode_title.replace(' ','_').replace('__','_')
    print(videoname , ep_title)
    try:
        if  ep_title.lstrip('_').split('_',1)[1] in videoname:
            pass
        else:
            videoname = (f"{videoname}_{ep_title}")
    except:
        pass
    try:
        # reorder the videoname to put S01E01 at the end
        m = re.search(r"(\w*)(_S\d{2}E\d{2})(\w*)", videoname)
        a = m.group(1)
        b = m.group(2)
        c = m.group(3).lstrip('_')
        if not c == 'None':
            videoname = f"{a}_[{c}]{b}".replace('_[]','') # if c is none remove empty []
    except:
        pass
    videoname = clean(videoname)
    spinner.stop()
    if C4_USES_N_m3u8DLRE:

        get_streams(config.drm_today.video.url, decryption_key, videoname, encrypted_vod_stream.brand_title)
    else:
        get_streams_by_ytdlp(config.drm_today.video.url, decryption_key, videoname, encrypted_vod_stream.brand_title)
    
    print(f"Your files are in {DOWNLOAD_DIR}/C4/{encrypted_vod_stream.brand_title.replace(' ','_')}")
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

def run():

    
    title = PF.figlet_format(' A L L 4 ', font='smslant')
    console.print(f"[green]{title}[/]")
    strapline = "An All4 Video Search, Selector and Downloader.\n\n"
    console.print(f"[red]{strapline}[/red]")
    url = Prompt.ask("[green]Enter a video url with a number of the form xxxxxx-xxx at the end \n[/]" )
    main(url)
    cleanup()
    exit(0)

if __name__ == "__main__":
    run()
   