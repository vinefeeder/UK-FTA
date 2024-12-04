# A_n_g_e_l_a  20:09:2023
# script finds videos from a keyword search or direct URL entry.
# KEYWORD SEARCH is the best and easiest way to run this script.
# this version for UK-FTA series.

from httpx import Client
import json
from rich.console import Console
from beaupy import select, select_multiple
import subprocess
import sys
from pathlib import Path
import pyfiglet as PF
from termcolor import colored
import os
import time
from beaupy.spinners import *

console = Console()
global client


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))
from configs import  config
SAVE_PATH = Path(config.SAVEPATH)
try:
    SAVE_PATH.mkdir(exist_ok=True, parents=True)
except Exception as e:
    print(f"Error creating save directory. Have you set up your save folder from Config in the menu? \n {e}")

BRIGHT_YELLOW = '\033[93m'
BRIGHT_GREEN = '\033[92m'
CURSOR_UP_ONE = "\033[F"
ERASE_LINE = "\033[K"




def prettify(my_list):
    """
    Formats a list of three elements into a styled string using rich text formatting.

    Parameters:
    my_list (list): A list containing three elements to be formatted.

    Returns:
    str: A formatted string where the first two elements are displayed in green
         and the third element is displayed in cyan on a new line with indentation.
    """
    my_beaupystring = []
    one = my_list[0]
    two = my_list[1]
    three = my_list[2]

    my_beaupystring = f"[green]{one}, {two}[/green][cyan]\n\t{three}[/cyan]"
    return my_beaupystring



def get_session_id(client):
    """
    Posts a request to the suggestedtv.com API to obtain a session_id.

    Parameters:
    client (httpx.Client): An instance of the httpx client.

    Returns:
    str: The session_id as returned by the API.

    Raises:
    httpx.HTTPStatusError: If the API returns a status code that is not 200.
    """
    post_headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0',
        'Accept': '*/*',
        'Accept-Language': 'en-GB,en;q=0.5',
        'Referer': 'https://tptvencore.co.uk/',
        'api-key': 'zq5pyPd0RTbNg3Fyj52PrkKL9c2Af38HHh4itgZTKDaCzjAyhd',
        'tenant': 'encore',
        'Origin': 'https://tptvencore.co.uk',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'Priority': 'u=4',
    }

    json_data = {}

    response = client.post('https://prod.suggestedtv.com/api/client/v1/session', headers=post_headers, json=json_data)

    if response.status_code == 200:
        session_id = response.json()['id']
        return session_id
    else:   
        print(f"Error: {response.status_code} - {response.text}")



def do_search(search_term,client, session_id):
    """
    Perform a search on the TPTV Encore site.

    Args:
    search_term (str): The search term.
    client (httpx.Client): An instance of the httpx client.
    session_id (str): The session_id as returned by get_session_id.

    Returns:
    list: A list of selected items. Each item is a list containing the name,
    video_id and synopsis of the item.

    Raises:
    httpx.HTTPStatusError: If the API returns a status code that is not 200.
    """
    
    suggested_url = f"https://prod.suggestedtv.com/api/client/v2/search/{search_term}"



    suggested_headers = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Origin': 'https://tptvencore.co.uk',
    'Referer': 'https://tptvencore.co.uk/',
    }

    get_headers = suggested_headers.copy()
    get_headers['Access-Control-Request-Headers'] = 'session,tenant'
    get_headers['Access-Control-Request-Method'] = 'GET'   
    get_headers['session'] = session_id
    get_headers['tenant'] = 'encore'                                                                         
    response = client.get(suggested_url, headers=get_headers)
    if response.status_code == 200:
        pass
    else:
        print(f"Error: {response.status_code} - {response.text}")
        sys.exit(1)
    myitems = []       
    for item in response.json()['data']:
        if  item.startswith('collection_'):
            id = item.replace('collection_','')
            collection_url = f"https://prod.suggestedtv.com/api/client/v1/collection/by-reference/{id}?extend=label"
            response = client.get(collection_url, headers=get_headers)
            if response.status_code == 200:
                data = response.json()
                for item in data['children']:
                    
                    myitems.append(item['id'].replace('product_',''))
            else:
                print(f"Error: {response.status_code} - {response.text}")
                sys.exit(1)
        else:
            myitems.append(item.replace('product_',''))
            mystring = ",".join(myitems)
        
    continued_search_url = "https://prod.suggestedtv.com/api/client/v1/product?ids=" + mystring + "&extend=label"
    
    response = client.get(continued_search_url, headers=get_headers)
    beaupylist = []     
    beaupydict = {}
    if response.status_code == 200:
        data = response.json()
        
        for item in data['data']:
            vid_id = item['id']
            name = item['name']
            synopsis = item['description'].replace('\n', ' ')
            if len(synopsis) > 300:
                synopsis = f"{synopsis[:300]}  ...snip"
            # create dict with video name as key. 
            # Repeats will be stored under the same key,
            # thus duplicates will be removed
            beaupydict[name] = [vid_id,synopsis]

        for item in beaupydict:
            beaupylist.append([item, beaupydict[item][0], beaupydict[item][1]])
        selected = select_multiple(beaupylist,  preprocessor=lambda val: prettify(val), page_size=6, pagination=True)
        return selected

def download(selected):
    
    """
    Downloads a video from the provided video id.

    Parameters:
    selected (list): A list of lists, where the inner list contains the video name, video id, and synopsis.

    Notes:
    The video is downloaded in MKV format using the N_m3u8DL-RE command line tool.
    The video is saved to the /home/angela/Downloads/devine/ directory.
    """
    brcove_headers = {
        'Accept': '*/*',
        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'BCOV-Policy': 'BCpkADawqM1yq3Go9abHJ4lBZ0wrYStC-pS1W01hdlACHxsiIz9AvQXy1wa3iqyd6yVJLXLZnZjFkKI2BCJjbtxiJqyPMZjIezEWKrI1TTSbugkD6dAXs7Ucxq09P9zQ8ZRU4ZjTa83VFhiL',
        'Connection': 'keep-alive',
        'Origin': 'https://tptvencore.co.uk',
        'Referer': 'https://tptvencore.co.uk/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
    }
    for select in selected:
        name = select[0]
        vid_id = select[1]

        response = client.get(
            f'https://edge.api.brightcove.com/playback/v1/accounts/6272132012001/videos/{vid_id}',
            headers=brcove_headers
        )

        if response.status_code == 200:    
            
            myjson = json.loads(response.content)
            
            manifest = myjson['sources'][0]['src']
            

            command = [
                'N_m3u8DL-RE',
                manifest,
                '--auto-select',
                '--save-name',
                name,
                '--save-dir',
                SAVE_PATH,
                '-mt',
                '-M',
                'format=mkv:muxer=mkvmerge',
                '--no-log'
            ]

            subprocess.run(command)
def doactionselect(client, session_id):
    
    actions = [
        "[green]Search by Keyword(s)",
        '[red]Download by URL[/red]',
        '[yellow]Quit[/]'
    ]
    action = select(actions, cursor="🢧", cursor_style="cyan")
    
    if 'Keyword(s)' in action:
        search_term = input("Enter a search term: ")
        selected = do_search(search_term, client, session_id)
        download(selected)
    elif 'Download' in action:
        url = input("Enter a URL: ")
        name = input("Enter the video's title: ")
        vid_id = url.split('/')[-1].split('-')[-1]
        selected = []
        selected.append([name,vid_id])
        download(selected)

   
    elif 'Quit' in action:
        print("Exiting...")
        exit(0)

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
        time.sleep(3)
        spinner.stop()     
        os.system('reset') 
    return  


if __name__ == '__main__':
    client = Client()
    title = PF.figlet_format('TPTV Encore', font='smslant')
    print(colored(title, 'green'))
    strapline = "A TPTV Encore: Video Search, Selector and Downloader.\n\n"
    print(colored(strapline, 'red'))   

    session_id  = get_session_id(client)
    doactionselect(client, session_id)
    cleanup()
    
    
    
