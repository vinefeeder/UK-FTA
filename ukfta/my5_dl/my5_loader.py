# Angela May:2024
# see config.py to set save path

import jmespath
from httpx import Client
import json, re
import sqlite3
from sqlite3 import Error
from beaupy import  select, select_multiple
from beaupy.spinners import *
import pyfiglet as PF
from rich.console import Console
from rich.prompt import Prompt
import sys
import my5getter as my5

sys.path.append("../")


client = Client(timeout=10)
console = Console()

CURSOR_UP_ONE = "\033[F"
ERASE_LINE =  "\033[K"

BRIGHT_YELLOW = '\\033[93m'
BRIGHT_GREEN = '\\033[92m'

SINGLEEPISODE = False

PAGE_SIZE = 12
ROW_COUNT = 12

def create_connection(): 
    conn = None
    try:
        conn = sqlite3.connect(':memory:')
    except Error as e:
        print(e)
    return conn

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

def keywordsearch(search):
    print("searching", end=' ')
    spinner = Spinner(DOTS)
    spinner.start()  
    client = Client(
        headers={
            'user-agent': 'Dalvik/2.9.8 (Linux; U; Android 9.9.2; ALE-L94 Build/NJHGGF)',
            'Host': 'corona.channel5.com',
            'Origin': 'https://www.channel5.com',
            'Referer':'https://www.channel5.com/',
        }) 

    url = f"https://corona.channel5.com/shows/search.json?platform=my5desktop&friendly=1&query={search}"
    try:  
        response = client.get(url)
        if response.status_code == 200:
            myjson = response.json()
        else:
            print (f"Response gave an error {response.status_code} \n {response.content}")
            sys.exit(0) 
        #console.print_json(data=myjson)
    except:
        spinner.stop()
        return None
    res = jmespath.search("""
    shows[].{
    slug: f_name,
    synopsis: s_desc
    } """,  myjson)
    beaupylist = []
    for i in range(0 ,len(res)):
        slug = (res[i]['slug'])
        synopsis = res[i]['synopsis']
        strtuple = (f"{i} {slug.title()}\n\t{synopsis}")
        beaupylist.append(strtuple)
    spinner.stop()

    found = select(beaupylist, preprocessor=lambda val: prettify(val), cursor="🢧", cursor_style="cyan", page_size=PAGE_SIZE, pagination=True)

    ind = found.split(' ')[0]
    url = f"https://corona.channel5.com/shows/{res[int(ind)]['slug']}/seasons.json?platform=my5desktop&friendly=1"
    #print(url)
    return url

def get_single_episode(brndslug, url):
    print("Getting single episode directly ..")
    my5.main(f"https://corona.channel5.com/show/{brndslug}")
    my5.cleanup()
    exit(0)


def get_next_data(brndslug, url):
    totalvideos = 0
    spinner = Spinner(DOTS)
    spinner.start()
    con, cur = create_database()
    # get seasons list
    response = client.get(f"https://corona.channel5.com/shows/{brndslug}/seasons.json?platform=my5desktop&friendly=1")
    if response.status_code == 200:
        myjson = json.loads(response.content)
    res = jmespath.search("""
    seasons[*].{
    seasonNumber: seasonNumber,
    sea_f_name: sea_f_name
    } """,  myjson)
    beaupylist = []
    # create list of season urls to get episodes
    # for i in range seasons
    urllist = []
    for i in range(0 ,len(res)):
        if res[i]['seasonNumber'] == None:
            res[i]['seasonNumber'] = '0'
            spinner.stop()
            return get_single_episode(brndslug,url)
        if  res[i]['sea_f_name'] == None:
            res[i]['sea_f_name'] = "unknown"

        urllist.append(f"https://corona.channel5.com/shows/{brndslug}/seasons/{res[i]['seasonNumber']}/episodes.json?platform=my5desktop&friendly=1&linear=true")
    allseries = []   
    for url in urllist:
        response = client.get(url)
        if response.status_code == 200:
            myjson = response.json()
            #console.print_json(data = myjson)
        else:
            print (f"Response gave an error {response.status_code} \n {response.content}")
            sys.exit(0)
        # odd case has nill results
        # question episodes
        MOVIE = False  
        
        results = jmespath.search("""
        episodes[*].{
        title: title,
        sea_f_name: sea_f_name,
        f_name: f_name,
        sea_num: sea_num,
        ep_num: ep_num                         
        } """,  myjson)
        if results == []:
            headers = {

                'Accept': 'application/json, text/plain, */*',
                'Host': 'corona.channel5.com',
                'Origin': 'https://www.channel5.com',
                'Referer': 'https://www.channel5.com/',
            }
            url = f"https://corona.channel5.com/shows/{brndslug}/episodes/next.json?platform=my5desktop&friendly=1"
            response = client.get(url, headers=headers)
            if response.status_code == 200:
                myjson = response.json()
            else:
                print (f"Response gave an error {response.status_code} \n {response.content}")
                sys.exit(0) 
        
        for i in range (0 , len(results)):
            totalvideos += 1
            if not MOVIE:
                url = f"https://www.channel5.com/show/{brndslug}/{results[i]['sea_f_name']}/{results[i]['f_name']}"
                
                sql = f''' INSERT OR IGNORE INTO videos(series, episode, url) VALUES('{results[i]['sea_num']}','{results[i]['ep_num']}','{url}');'''
            else:
                url = f"https://www.channel5.com/show/{results['sh_f_name']}/"
                spinner.stop()
                infoline = "[info] Detected a single Movie; downloading directly\n\n"
                console.print(f"[green]{infoline}[/green]")
                my5.main(url)
                my5.cleanup()
                sys.exit(0)
            allseries.append(results[i]['sea_num'])
            cur.execute(sql)
    spinner.stop()

    while True:
        if totalvideos <= ROW_COUNT: 
            search = '0'  
            break
        else:
            unique_list = list(dict.fromkeys(allseries))
            print_back(2, "Series found are:-")
            for item in unique_list:
                console.print(f"[pink1]{item}[/pink1]", end = ' ')
            console.print(f"[green]\nThere are over {ROW_COUNT} videos to display.\n\
            Enter the series number(s) to see a partial list,\n\
            or enter [pink1]'0'[/pink1] to show all episodes available[/green]\n\
            [red]Separate series numbers with a space \n[/red]")

            search = Prompt.ask("? ")
            if not re.match("^[0-9]{1,2}", search):
                print ("Use only numbers and Spaces!")
            else:
                break
            
    if search == '0':
        cur.execute("SELECT * FROM videos")

    elif type(search) != int:
        srchlist = search.split(' ')
        partsql = "SELECT * FROM videos WHERE series='"
        for srch in srchlist:
            partsql = f"{partsql}{srch}' OR series='"
        partsql = partsql.rstrip(" OR series='")
        sql = partsql + "';"
        cur.execute(sql)

    else:
        search = "Series " + search
        cur.execute("SELECT * FROM videos WHERE series=?", (search,))
    rows = cur.fetchall()
    if len(rows)==0:
        my5.main(url)
        exit(0)
    con.close()
    beaupylist = []
    index = [] 
    inx = 0
    for col in rows:
        beaupylist.append(f"{col[1]} {col[2]} {col[3]}")
        index.append(inx)
        inx+=1
    return index, beaupylist

def dobrowse(url):
    beaupylist = []
    response = client.get(url, follow_redirects=True)
    if response.status_code != 200:
        print (f"Response gave an error {response.status_code} \n {response.content}")
        sys.exit(0)
    myjson = response.json()
    #console.print_json(data=myjson)
    #shows►0►id
    myjson = myjson['shows']

    for i in range (len(myjson)):
        #id = myjson[i]['id']
        title = myjson[i]['title']
        #f_name = myjson[i]['f_name']
        synopsis = myjson[i]['s_desc']
        
        beaupylist.append(f"{i} {title}\n\t{synopsis}")
    found = select(beaupylist,  preprocessor = lambda val: prettify(val), cursor="🢧", cursor_style="cyan", page_size=PAGE_SIZE, pagination=True)
    found_index = int(found.split(' ')[0])
    url = f"https://https://www.channel5.com/show/{myjson[found_index]['f_name']}"
    #print(url)
    return url

def prettify(val):
    try:
        parts = val.split('\t') 
        title = f"[green]{parts[0]}[/green]"  
        synopsis = f"[cyan]{parts[1]}[/cyan]"  
        return f"{title}\t{synopsis}"
    except:
        return f"[green]{val}[/green]"
    
def dobrowseselect():

    # 2nd level action choice
    # provide list of categories to browse
    # calls dobrowse(url)
    fn = []
    for key in media_dict.keys():
        fn.append(key)
        
    action = select(fn, preprocessor = lambda val: prettify(val), cursor="🢧", cursor_style="cyan")
    browse_url = media_dict[action]
    url = dobrowse(browse_url)
    return url

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
            #https://corona.channel5.com/shows/coma-186a64a9-434d-4d26-bc51-00a003bbe92d/episodes.json?platform=my5desktop&friendly=1
            break
        else:
            print("A correct URL has 'show' in the line")
    brandslug = url.split('/')[4]
    return f"https://corona.channel5.com/shows/{brandslug}"

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
        print_back(9,'') ## clear unwanted sceen text
        #os.system("python ukfta/my5_dl/my5getter.py")  ### don't like this call
        my5.run()
        # need a better entry point
        exit(0)
    elif 'Quit' in action:
        print("Exiting..")
        exit(0)
    else:
        return None

if __name__ == '__main__':
    title = PF.figlet_format(' My5 ', font='smslant')
    console.print(f"[green]{title}[/green]")
    strapline = "A My5 Video Search, Selector and Downloader.\n\n"
    console.print(f"[red]{strapline}[/red]\n\n[green]Use 🔺🔻 to scroll[/green]\n")
    
    media_dict = {
        'Films': 'https://corona.channel5.com/shows/search.json?platform=my5desktop&friendly=1&vod_subgenres%5B%5D=6100117389032&vod_subgenres%5B%5D=6100117390032&vod_subgenres%5B%5D=6100117391032',
        'Documentary': 'https://corona.channel5.com/shows/search.json?platform=my5desktop&friendly=1&vod_subgenres[]=6100110273032&vod_subgenres[]=6100105092032&vod_subgenres[]=6100105093032&vod_subgenres[]=6100105094032&vod_subgenres[]=6100105095032&vod_subgenres[]=6100105096032&vod_subgenres[]=6100105097032&vod_subgenres[]=6100110268032&vod_subgenres[]=6100110269032&vod_subgenres[]=6100110270032&vod_subgenres[]=6100110271032&vod_subgenres[]=6100110272032',
        'Crime': 'https://corona.channel5.com/shows/search.json?platform=my5desktop&friendly=1&limit=100&sort_by=popular&offset=0&vod_subgenres%5B%5D=7626766659032&vod_subgenres%5B%5D=7626766660032',
        'Dramas & Soaps': 'https://corona.channel5.com/shows/search.json?platform=my5desktop&friendly=1&vod_subgenres%5B%5D=6100110274032&vod_subgenres%5B%5D=6100110275032',
        'Entertainment': 'https://corona.channel5.com/shows/search.json?platform=my5desktop&friendly=1&vod_subgenres%5B%5D=6100112646032&vod_subgenres%5B%5D=6100110276032&vod_subgenres%5B%5D=6100110277032&vod_subgenres%5B%5D=6100112638032&vod_subgenres%5B%5D=6100112639032&vod_subgenres%5B%5D=6100112640032&vod_subgenres%5B%5D=6100112641032&vod_subgenres%5B%5D=6100112642032&vod_subgenres%5B%5D=6100112643032',
        'Science and Nature': 'https://corona.channel5.com/shows/search.json?platform=my5desktop&friendly=1&vod_subgenres%5B%5D=6100118658032&vod_subgenres%5B%5D=6100117395032&vod_subgenres%5B%5D=6100117396032&vod_subgenres%5B%5D=6100117397032',
        'Sport': 'https://corona.channel5.com/shows/search.json?platform=my5desktop&friendly=1&vod_subgenres%5B%5D=6100118660032',
        'Travel': 'https://corona.channel5.com/shows/search.json?platform=my5desktop&friendly=1&vod_subgenres%5B%5D=6100118664032&vod_subgenres%5B%5D=6100118662032&vod_subgenres%5B%5D=6100118663032',
        'Real Lives': 'https://corona.channel5.com/shows/search.json?platform=my5desktop&friendly=1&vod_subgenres%5B%5D=6100117393032',
        'Lifestyle': 'https://corona.channel5.com/shows/search.json?platform=my5desktop&friendly=1&vod_subgenres%5B%5D=6100114865032&vod_subgenres%5B%5D=6100114859032&vod_subgenres%5B%5D=6100114860032&vod_subgenres%5B%5D=6100114861032&vod_subgenres%5B%5D=6100114862032&vod_subgenres%5B%5D=6100114863032',
        'News & Current Affairs': 'https://corona.channel5.com/shows/search.json?platform=my5desktop&friendly=1&vod_subgenres%5B%5D=6726148277032',
        'Smithsonian': 'https://corona.channel5.com/shows/search.json?platform=my5desktop&friendly=1&ids%5B%5D=7200164903527&ids%5B%5D=4365811271527&ids%5B%5D=4301348409527&ids%5B%5D=4783938314527&ids%5B%5D=4977961314527&ids%5B%5D=5600080444527&ids%5B%5D=4489370797527&ids%5B%5D=4617233242527&ids%5B%5D=6638446529527&ids%5B%5D=6275149260527&ids%5B%5D=7810836259527&ids%5B%5D=7741736837527&ids%5B%5D=8103343367527&ids%5B%5D=8103392205527&ids%5B%5D=8103519133527&ids%5B%5D=8103520030527&ids%5B%5D=5285427795527&ids%5B%5D=4867434237527&ids%5B%5D=4301367810527&ids%5B%5D=7059359470527&ids%5B%5D=8164734673527&ids%5B%5D=8164998660527&ids%5B%5D=8165160044527',
        'Milkshake': 'https://corona.channel5.com/shows/search.json?platform=my5desktop&friendly=1&vod_subgenres%5B%5D=6100114867032',
    
    }
    media_dict = dict(sorted(media_dict.items(), key=lambda x: x[0]))
    

    url = doactionselect()

            
    slug = url.split('/')[-1]
    if 'json' in slug:
        slug = url.split('/')[-2]
    
    index, beaupylist = get_next_data(slug,url)
    
    links = select_multiple(beaupylist,   preprocessor = lambda val: (f"[green]{val}[/green]"), minimal_count=1, page_size=PAGE_SIZE, pagination=True)
    
    for link in links:
        url = link.split(' ')[2]
        # run the link in my5getter.py
        my5.main(url)
    my5.cleanup()
