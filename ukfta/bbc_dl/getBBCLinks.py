import subprocess
import sqlite3
from sqlite3 import Error
from beaupy import select, select_multiple
from beaupy.spinners import *
import os
import subprocess
from termcolor import colored
import pyfiglet as PF
import time
import re
import jmespath
from httpx import Client
from rich.prompt import Prompt
from rich.console import Console
from glob import glob
from pathlib import Path
import sys
from scrapy import Selector
import json
import BBC


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))
from configs import  config

CURSOR_UP_ONE = "\033[F"
ERASE_LINE =  "\033[K"

BRIGHT_YELLOW = '\\033[93m'
BRIGHT_GREEN = '\\033[92m'
BRIGHT_RED = '\\033[91m'

INDEX = False
client = Client()
console=Console()
PAGE_SIZE = 12
ROW_COUNT = 12

# configs not found while developing; trap error
try:
    SAVE_PATH = config.SAVEPATH
except:
    SAVE_PATH = SCRIPT_DIR

def create_connection(): 
    conn = None
    try:
        conn = sqlite3.connect(':memory:')
    except Error as e:
        print(e)
    return conn
def pad_number( match):
    number = int(match.group(1))
    return format(number, "02d")



def populatetable(pid):
    # prepare sql table iplayer in memory
    global con, cur
    con = create_connection()
    cur = con.cursor()

    sql = '''
    CREATE TABLE IF NOT EXISTS iplayer(
    rowid INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR,
    series VARCHAR,
    episode VARCHAR,
    pid VARCHAR 
    );
    '''
    ## prepare sql table iplayer in memory
    
    cur.execute(sql)
        
    if os.name == 'posix':
        iplayer = 'get_iplayer'
    else:
        iplayer = 'get_iplayer.cmd' 
    command = [
        iplayer,
        '--nocopyright',
        '-q',
        '--pid-recursive-list',
        '--pid',
        pid,
    ]

    #get pid list from get_iplayer and store in sqlite3-table iplayer
    moreresults = subprocess.run(command, capture_output=True, \
                               text=True, stderr=None)
    mylines = str(moreresults).split('\\n')
    count = 0
    allseries = []
    for line in mylines:
        if 'Episodes' in line:
            pass
        elif count <=1: # ignore get_iplayer waste
            pass
        else:
            pid = pid.lstrip()
            try:
                if len(line.split(',')) == 4:
                    line = line.replace(',', '', 1)
                fulltitle, waste, pid = line.split(',')
                fulltitle = fulltitle.replace("'",'') # apostrophes foul anything database related!
                colon_count = fulltitle.count(':')
                titleparts = fulltitle.split(':')
                if colon_count>1:
                    title = titleparts[0]  # 'Amazing Hotels'
                    series = titleparts[2].split('-')[0].strip()  # 'Series 1'
                    episode = titleparts[2].split('-')[1].strip()
                else:
                    title = titleparts[0]
                    series = titleparts[1].split('-')[0].strip()
                    episode = titleparts[1].split('-')[1].strip()
                if len(series) >=  10: # trailers have text which upset ongoing logic so remove
                    pass
                else:
                    allseries.append(series)  #
                
                sql = f''' INSERT OR IGNORE INTO iplayer(title, series,\
                      episode, pid) VALUES('{title}','{series}','{episode}','{pid}');'''
                cur.execute(sql)
            except:
                try:
                    titleparts = fulltitle.split('-' )
                    title = titleparts[0]
                    if count > 12:
                        series = 'Series 001'  # code for 'special'; not essential part of series.
                    else:
                        # no series # listed so provide one
                        series = 'Series 1'
                    episode = titleparts[1].strip()
                    sql = f''' INSERT OR IGNORE INTO iplayer(title, series,\
                          episode, pid) VALUES('{title}','{series}','{episode}','{pid}');'''
                    cur.execute(sql)
                    total = cur.lastrowid
                except:
                    break
                pass # 2 lines of garbage at end
        count += 1

    # remove two garbage lines
    sql = f'DELETE FROM iplayer where rowid BETWEEN {total-1} AND {total};'
    cur.execute(sql)
    return allseries


def keywordsearch(search):
    print("searching", end=' ')
    spinner = Spinner(DOTS)
    spinner.start()  

    headers = {
            'Accept': '*/*',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',
            'Origin': 'https://www.bbc.com',
            'Referer': 'https://www.bbc.com/',
        }
    client = Client()
    url = f"https://ibl.api.bbc.co.uk/ibl/v1/new-search"
        #url = f"https://search.api.bbci.co.uk/formula/iplayer-ibl-root?q={search_term}&apikey=D2FgtcTxGqqIgLsfBWTJdrQh2tVdeaAp&seqId=0582e0f0-b911-11ee-806c-11c6c885ab56"
    params = {
        'q': search,
        'rights': 'web',
        'mixin': 'live'
    }
    try:
        response = client.get(url, headers=headers, params=params, follow_redirects=True)
        if response.status_code != 200:
            raise Exception("Failed to retrieve data.")
        html = response.text
        
        parsed_data = json.loads(html)  # to json
        #console.print_json(data=parsed_data)
    except Exception as e:
        print(f'No valid data returned for {url} error was {e}')
        return
    spinner.stop()
  
    res = jmespath.search("""
    new_search.results[*].{
    title: title,
    synopsis: synopses.small,
    url: id
    } """,  parsed_data)

    beaupylist = []
    for i in range(0 ,len(res)):
        #title = (next (item for item in (res[i]['title']) if item is not None))
        title = res[i]['title']
        synopsis = res[i]['synopsis']
        url = res[i]['url']
        #url = rinseurl(url) 
        beaupylist.append(f"{i} {title}\t{synopsis}")
        
    spinner.stop()
    found = select(beaupylist,  preprocessor=lambda val: prettify(val), cursor="🢧", cursor_style="cyan", page_size=PAGE_SIZE, pagination=True)
   
    ind = int(found.split(' ')[0])
    print(res[ind])
    pid = res[ind]['url']
    #pid = found.split('/')[-1]   
    return pid

def main(pid):
    beaupylist = []
    allseries = populatetable(pid)
    unique_list = list(dict.fromkeys(allseries))
    chars = set('IVXMD')
    
    if len(allseries) >= ROW_COUNT: 
        
        print_back(2, "Series found are:-")
        
        console.print(f"[green]There are over {ROW_COUNT} videos to display[/]")
        console.print("[green]Enter the series number(s) to see a partial list, \nor enter [pink1]'0'[/pink1] to show all episodes available[/green]")
        console.print("[red]Separate series numbers with a space [/red]")
        console.print("[info] Series found are:-")
        
        
        for item in unique_list:
            if 'Series' in item:
                item = item.replace('Series ', '')
                console.print(f"[pink1]{item}[/pink1]" , end=' ')
            elif any((c in chars) for c in item):
                print("Roman Numerals found  - select all series using '0'")
                break

        search = input ('Series Nos? ')
    else:
        search = '0'
        
    if search == '0':
        cur.execute("SELECT * FROM iplayer")

    elif type(search) != int:
        srchlist = search.split(' ')
        partsql = "SELECT * FROM iplayer WHERE series='Series "
        for srch in srchlist:
            partsql = f"{partsql}{srch}' OR series='Series "
        partsql = partsql.rstrip(" OR series='Series ")
        sql = partsql + "';"
        cur.execute(sql)

    else:
        search = "Series " + search
        cur.execute("SELECT * FROM iplayer WHERE series=?", (search,))
    rows = cur.fetchall()
    index = []
    #rows = sorted(rows, key=lambda x: x[:8])
    for row in rows:
        ind, title, series, episode, pid = row
        index.append(ind-1)
        if INDEX:
            beaupylist.append(f"{ind} {title} {series} {episode} \t{pid}")
        else:
            beaupylist.append(f"{title} {series} {episode} \t{pid}")

    if len(rows)==0:
        print("[info] No series of that number found. Exiting. Check and try again. ")
    con.close()
    beaupylist = sorted(beaupylist, key=lambda x: x[:-8])
    selected =  select_multiple(beaupylist, page_size=PAGE_SIZE, pagination=True)

    for select in selected:
        videoname = select.split('\t')[0]
        #fix videoname
        videoname = re.sub(r"(\d+)", pad_number, videoname).lstrip(' ').rstrip(' ') 
        replacements=[("Series ", "S"), (" Episode ", "E")]
        for pat,repl in replacements:
            videoname = re.sub(pat, repl, videoname)
        videoname = videoname.replace(' ', '_').rstrip('_')
        # sanity check
        if videoname.endswith('__S01'): #one-off video
            videoname = videoname.replace('__S01','')


        pid = select.split('\t')[1]
        
        spinner = Spinner(DOTS)
        spinner.start()
        os.system(f"get_iplayer --nocopyright --output ./ --streaminfo --pid {pid} >> stream.txt")
        os.system(f"get_iplayer --nocopyright --output ./ --subtitles-only --pid {pid}")
        for f in glob('*.srt'):
            os.rename( f, "subs.srt")
        spinner.stop()
        BBC.dodownload(videoname)
        os.remove("stream.txt")
        
def sorted_nicely( l ): 
    """ Sort the given iterable in the way that humans expect.""" 
    convert = lambda text: int(text) if text.isdigit() else text 
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
    return sorted(l, key = alphanum_key)
        
def dobrowse(url: str):
    
    resp = client.get(url)
    if resp.status_code != 200:
        print("Error: ", resp.status_code)
        return exit(1)
    sel = Selector(text=resp.text)
    init_data = (sel.xpath('//*[@id="tvip-script-app-store"]')).get()
    init_data = init_data.replace('<script id="tvip-script-app-store">window.__IPLAYER_REDUX_STATE__ = ', '').replace(';</script>', '')
    init_data = json.loads(init_data)

    # testing
    #file = open("init_data.json", "w")
    #file.write(json.dumps(init_data))
    f#ile.close()
    #console.print_json(data=init_data)

    try:
        # Search for the nested episode data
        episode_data = jmespath.search("bundles[].entities[].episode", init_data)
        # convert wanted data into a flat list
        res = jmespath.search("""
            [*].{
            title: title.default,
            synopsis: synopsis.small 
            id: id
            } """,  episode_data)

    except Exception as e:
        print(f"An error occurred while using jmespath to extract episode data: {e}")
    beaupylist = [] 

    for i in range (len(res)):
        beaupylist.append(f"{i} | {res[i]['title']} | \n\t{(res[i]['synopsis'])}")
        beaupylist = list(set(beaupylist))  # remove duplicates but left unsorted
        beaupylist = sorted(beaupylist, key=lambda x: int(x[:2])) # sort on first two numbers
    
    found = select(beaupylist, cursor="🢧", cursor_style="cyan" , preprocessor = lambda val: prettify(val),  page_size=PAGE_SIZE, pagination=True)
    f = found.split('|')[0]
    id = res[int(f)]['id']  # programme id
    # get series pid
    url = f"https://www.bbc.co.uk/programmes/{id}.json"
    resp = client.get(url)
    if resp.status_code != 200:
        print("Error: ", resp.status_code)
        return exit(1)
    resp = resp.content 
    data = json.loads(resp)
    #programme►parent►programme►parent►programme►pid
    try:
        pid = data['programme']['parent']['programme']['parent']['programme']['pid']
    except:
        pid = id
    return pid
        
def dobrowseselect():

    # 2nd level action choice
    # provide list of categories to browse
    # calls dobrowse(url)
    fn = []
    for key in media_dict.keys():
        fn.append(key)
        
    action = select(fn, cursor="🢧", cursor_style="cyan")
    browse_url = media_dict[action]
    url = dobrowse(browse_url)
    return url
        
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
        
def doactionselect():
    # top level choice for action
    fn = [
        "[green]Search by Keyword(s)",
        "Greedy Search by URL",
        'Browse by Category[/]',
        '[red]Download by URL[/red]',
        '[yellow]Quit[/]'
        ]
    action = select(fn, cursor="🢧", cursor_style="cyan")
    if 'Keyword(s)' in action:
        return dosearch()
    elif 'Greedy' in action:
        return dourlentry()
    elif 'Browse' in action:
        
        return dobrowseselect()
    elif 'Download' in action:
        #print_back(7,'') ## clear unwanted sceen text
        BBC.run()
        #cleanup()
        exit(0)
    elif 'Quit' in action:
        print("Exiting..")
        exit(0)
        
def dourlentry():
    # 2nd level action Enter URL
    url = Prompt.ask("[red]Enter URL: [/red]")
    return url

def print_back(n=1, text='a'): 
    for _ in range(n): 
        sys.stdout.write(CURSOR_UP_ONE) 
        sys.stdout.write(ERASE_LINE)
    console.print(f"[bright_yellow]{text}[/bright_yellow]") 
    

def prettify(val):
    # this is a custom prettifier for the items in beaupylist
    try:
        parts = val.split('\t')
        #item = BeaupyItem(title=parts[0], synopsis=parts[1])
        return f"[green]{parts[0]}[/green]\t[cyan]{parts[1]}[/cyan]"
    except (IndexError, ValueError):
        return f"[green]{val}[/green]"

    
def cleanup():
    ###############################################################################################
    # The beaupy or rich module that produces checkbox lists/colours seems to clog and confuse my 
    # linux box's terminal; 
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
    
if __name__ == '__main__':
    title = PF.figlet_format(' B B C ', font='smslant')
    print(colored(title, 'green'))
    strapline = "A BBC Video Selector and Downloader.\n\n"
    print(colored(strapline, 'red'))
    
    media_dict = {
        
        'Arts': 'https://www.bbc.co.uk/iplayer/categories/arts/featured',
        'Comedy': 'https://www.bbc.co.uk/iplayer/categories/comedy/featured',
        'Documentaries': 'https://www.bbc.co.uk/iplayer/categories/documentaries/featured',
        'Drama-and-soaps': 'https://www.bbc.co.uk/iplayer/categories/drama-and-soaps/featured',
        'Entertainment': 'https://www.bbc.co.uk/iplayer/categories/entertainment/featured',
        'Films': 'https://www.bbc.co.uk/iplayer/categories/films/featured',
        'Food': 'https://www.bbc.co.uk/iplayer/categories/food/featured',
        'History': 'https://www.bbc.co.uk/iplayer/categories/history/featured',
        'Lifestyle': 'https://www.bbc.co.uk/iplayer/categories/lifestyle/featured',
        'Music': 'https://www.bbc.co.uk/iplayer/categories/music/featured',
        'News': 'https://www.bbc.co.uk/iplayer/categories/news/featured',
        'Science-and-nature': 'https://www.bbc.co.uk/iplayer/categories/science-and-nature/featured',
        'Sport': 'https://www.bbc.co.uk/iplayer/categories/sport/featured',
        'Archive': 'https://www.bbc.co.uk/iplayer/categories/archive/featured',
    }
    
    pid = doactionselect()
    main(pid)
    cleanup()
