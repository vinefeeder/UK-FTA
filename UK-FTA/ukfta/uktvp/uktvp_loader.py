# A_n_g_e_l_a  23:09:2023  
# refactored June 2024

# script finds videos from a keyword search or direct URL entry.
# Greedy-search lists all series videos on request,
# waits for user selection before download
# uses an external downloader slimitvx.py
# both uktvp_loader.py and slimuktvp.py must be
# in the same folder.

import jmespath
from httpx import Client
import json, re, os
import sqlite3
from sqlite3 import Error
from beaupy import  select, select_multiple
from beaupy.spinners import *
import time
import pyfiglet as PF
from termcolor import colored
from rich.console import Console
import slimuktvp as tvp
from rich.prompt import Prompt
import sys
import slimuktvp as uktvp

client = Client()
console = Console()

CURSOR_UP_ONE = "\033[F"
ERASE_LINE =  "\033[K"

BRIGHT_YELLOW = '\\033[93m'
BRIGHT_GREEN = '\\033[92m'

PAGE_SIZE = 12

# database in memory
def create_connection(): 
  con = None;
  try:
      con = sqlite3.connect(':memory:')
  except Error as e:
      print(e)
  return con

def create_database():
    con = create_connection()
    cur = con.cursor()

    sql = '''
    CREATE TABLE IF NOT EXISTS videos(
    rowid INTEGER PRIMARY KEY AUTOINCREMENT,
    series VARCHAR,
    episode VARCHAR,
    url VARCHAR,
    UNIQUE (url) 
    );
    '''
    cur.execute(sql)
    return con, cur

def rinseurl(string):
    illegals = "*'%$!(),;"  # safe for urls
    string = ''.join(c for c in string if c.isprintable() and c not in illegals)
    string = string.lstrip(' ')
    return string

def get_next_data(brand_slug):
    spinner = Spinner(DOTS)
    spinner.start()
    connection, cursor = create_database()
    response = client.get(f"https://vschedules.uktv.co.uk/vod/brand/?slug={brand_slug}")
    if response.status_code != 200:
        print(f"Response gave an error {response.status_code} \n {response.content}")
        exit(0)

    series_ids = [series['id'] for series in json.loads(response.content)['series']]
    video_data = []

    for series_id in series_ids:
        response = client.get(f"https://vschedules.uktv.co.uk/vod/series/?id={series_id}")
        if response.status_code != 200:
            print(f"Error fetching series data\nResponse gave an error {response.status_code} \n {response.content}")
            exit(0)
        series_number = int(json.loads(response.content)['number'])
        total_episodes = int(json.loads(response.content)['total_episodes'])

        for episode_index in range(total_episodes):
            episode_data = json.loads(response.content)['episodes'][episode_index]
            episode_number = episode_data['episode_number']
            video_id = episode_data['watch_online_link'].split('/')[6]
            video_url = f"https://uktvplay.co.uk/shows/{brand_slug}/series-{series_number}/episode-{episode_number}/{video_id}"
            video_data.append((series_number, episode_number, video_url))
            sql = f"INSERT OR IGNORE INTO videos(series, episode, url) VALUES(?, ?, ?);"
            cursor.execute(sql, (series_number, episode_number, video_url))

    spinner.stop()

    while True:
        if len(video_data) <= 16:
            search_input = '0'
            break
        else:
            unique_series = list(set(series_number for series_number, _, _ in video_data))
            print_back(2, "Series found are:-")
            for series_number in unique_series:
                console.print(f"[pink1]{series_number}[/pink1]", end=' ')
            console.print(
                "[green]\nThere are over 16 videos to display.\n"
                "Enter the series number(s) to see a partial list,\n"
                "or enter [pink1]'0'[/pink1] to show all episodes available[/green]\n"
                "[red]Separate series numbers with a space \n[/red]")

            search_input = Prompt.ask("? ")
            if not re.match("^[0-9]{1,2}", search_input):
                print("Use only numbers and Spaces!")
            else:
                break

    if search_input == '0':
        cursor.execute("SELECT * FROM videos")
    elif search_input.isdigit():
        search_input = int(search_input)
        cursor.execute("SELECT * FROM videos WHERE series=?", (search_input,))
    else:
        search_input = [int(series_number) for series_number in search_input.split(' ')]
        part_sql = "SELECT * FROM videos WHERE series IN " + ','.join('?' for _ in search_input)
        cursor.execute(part_sql, search_input)
    
    video_data = [(series, episode, url) for _, series, episode, url in cursor.fetchall()]

    return [index for index, (_, _, _) in enumerate(video_data)], [f"{series} {episode} {url}" for series, episode, url in video_data]

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
        #os.system('reset')
    return
    

def keywordsearch(search):
    print("searching", end=' ')
    spinner = Spinner(DOTS)
    spinner.start()  
    client = Client(
        headers={
            'user-agent': 'Dalvik/2.9.8 (Linux; U; Android 9.9.2; ALE-L94 Build/NJHGGF)',
            'Host': 'vschedules.uktv.co.uk',
            'Origin':'https://uktvplay.co.uk',
            'Referer':'https://uktvplay.co.uk/',
        }) 
    url = f"https://vschedules.uktv.co.uk/vod/search/?q={search}"
    response = client.get(url)
    myjson = response.json()  
    #console.print_json(data=myjson)
    res = jmespath.search("""
    [].{
    slug: slug,
    synopsis: synopsis
    } """,  myjson)

    beaupylist = []
    for i in range(0 ,len(res)):
        slug = (res[i]['slug'])
        title = slug.replace('-', '_').title()
        url = f"https://uktvplay.co.uk/{slug}/watch-online",
        url = rinseurl(url)
        synopsis = res[i]['synopsis']
        strtuple = (f"{i} {title}\t{synopsis}")
        beaupylist.append(strtuple)
    spinner.stop()
    found = select(beaupylist, preprocessor = lambda val: prettify(val), cursor="🢧", cursor_style="cyan", page_size=PAGE_SIZE, pagination=True)
    ind = found.split(' ',1)[0]
    slug = res[int(ind)]['slug']
    print(slug)
    return f"https://uktvplay.co.uk/{slug}/watch-online"

def doactionselect():
    # top level choice for action
    
    fn = [
        "[green]Search by Keyword(s)",
        "Greedy Search by URL",
        '[red]Download by URL[/red]',
        '[yellow]Quit[/]'
        ]
    action = select(fn, cursor="🢧", cursor_style="cyan")
    if 'Keyword(s)' in action:
        return dosearch()
    elif 'Greedy' in action:
        return dourlentry()

    elif 'Download' in action:
        print_back(9,'') ## clear unwanted sceen text
        uktvp.run()
        
        exit(0)
    elif 'Quit' in action:
        print("Exiting..")
        exit(0)
    else:
        return None
    
def print_back(n=1, text='a'): 
    for _ in range(n): 
        sys.stdout.write(CURSOR_UP_ONE) 
        sys.stdout.write(ERASE_LINE)
    console.print(f"[bright_yellow]{text}[/bright_yellow]")
    
def dosearch():
    # 2nd level action choice
    # run normal keyword search
    search = Prompt.ask('[cyan2]Enter key word(s) for search ')
    while len(search) <= 1:
        search = Prompt.ask('\n[red]Enter a search word\n')
        if search == "":
            print("Exiting..")
            exit(0)
        else:
            search = search.title()
            break 
    return keywordsearch(search)

def dourlentry():
    # 2nd level action Enter URL
    while True:
        url = Prompt.ask("[red]Enter URL: [/red]")
        if 'show' in url:
            url = url.encode('utf-8', 'ignore').decode().strip()
            
            break
        else:
            print("A correct URL has 'show' in the line")
    return url

def prettify(val):
    try:
        parts = val.split('\t')
        title = f"[green]{parts[0]}[/green]"  
        synopsis = f"[cyan]{parts[1]}[/cyan]"  
        return f"{title}\n\t{synopsis}"
    except:
        return f"[pink1]{val}[/pink1]"

if __name__ == '__main__':
    title = PF.figlet_format(' U ', font='smslant')
    print(colored(title, 'green'))
    strapline = "A U Video Search, Selector and Downloader.\n\n"
    print(colored(strapline, 'red'))
    
    url = doactionselect()
    n = url.count('/')
    if n == 4:
        slug = url.split('/')[3]
    else:
        slug = url.split('/')[4]

    index, beaupylist = get_next_data(slug)
    console.print(f"[green] 🔺🔻 to scroll[/green]\n")
    videos = select_multiple(beaupylist, preprocessor = lambda val: (f"[green]{val}[/green]"),  minimal_count=1, page_size=PAGE_SIZE, pagination=True)
    for video in videos:
        url = video.split(' ')[2]
        tvp.download(url)
    cleanup()
    exit(0)
    