# A_n_g_e_l_a
# Revision August 2024


from scrapy import Selector 
from httpx import Client
import re
import json
import stvgetter as stv
from beaupy import confirm, select, select_multiple
from beaupy.spinners import *
import pyfiglet as PF
from termcolor import colored
import gc
from pathlib import Path
import sqlite3
from sqlite3 import Error
from rich.console import Console
import os, time
console = Console()
from rich.prompt import Prompt
import os, sys
import jmespath

# GLOBALS

CURSOR_UP_ONE = "\033[F"
ERASE_LINE =  "\033[K"

BRIGHT_YELLOW = '\\033[93m'
BRIGHT_GREEN = '\\033[92m'

INTERRUPT = False
PAGE_SIZE = 8 # verbose STV 
ROW_COUNT = 12

client = Client()
DRM = False
# This list of media categories is incomplete; add more if required. Code will arrange them alphabetically
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
media_dict = {
        'Films': 'https://player.stv.tv/categories/movies',
        'Sport': 'https://player.stv.tv/categories/the-sport-hub',
        'Crime Dramas': 'https://player.stv.tv/categories/crime-drama',
        'True Crime': 'https://player.stv.tv/categories/crime-punishment',
        'Comedy Dramas': 'https://player.stv.tv/categories/comedy-drama',
        'Documentaries': 'https://player.stv.tv/categories/documentaries',
        'Dramas': 'https://player.stv.tv/categories/dramas',
        'Entertainment': 'https://player.stv.tv/categories/entertainment',
        'Soaps': 'https://player.stv.tv/categories/soaps',
        'Food': 'https://player.stv.tv/categories/food-lifestyle',
        'Scenic Scotland': 'https://player.stv.tv/categories/scenic-scotland',
        'News': 'https://player.stv.tv/categories/news-current-affairs',
        'Thrillers': 'https://player.stv.tv/categories/thrillers',
        'History Hit': 'https://player.stv.tv/categories/history-hit',
        'Real Crime': 'https://player.stv.tv/categories/real-crime',
        'Real Stories': '`https://player.stv.tv/categories/real-stories',
        'Real Life': 'https://player.stv.tv/categories/real-life',
    
}  
media_dict = dict(sorted(media_dict.items(), key=lambda x: x[0]))


# gets summmary page __NEXT_DATA__
def get_next_data(url ):
    spinner = Spinner(DOTS, "Collecting data - please wait ...")
    spinner.start()
    
    try:
        myhtml = client.get(url).text
    except Exception as e:
        if type(e).__name__ == 'TypeError':
            print("[info] STV's website reports nothing found for that keyword")
        else:
            print(f"[info] STV's website reports an error {e}")
            print("Check and try again.")
        spinner.stop()
        exit(0)
    
    sel = Selector(text = myhtml)
    selected = sel.xpath('//*[@id="__NEXT_DATA__"]').extract()
    selected = selected[0] 

    pattern = r'\s*({.*})\s*' 
    myjson = json.loads(re.search(pattern, selected).group())
    spinner.stop()
    
    try:      
        DRM = myjson['props']['pageProps']['data']['programmeData']['drmEnabled']
    except Exception as e:
        print(e)
        print("[info] STV's website reports the url invalid")
        print("Check and try again.")
        exit(0)
    if DRM:
        print("[info] The videos are encrypted and you will need to have a CDM installed and its location configured.") 
    try:
        # multi-series?  
        #pathexists = myjson['props']['pageProps']['data']['tabs'][1]['params']['query']['series.guid']
        spinner = Spinner(DOTS, "Collecting data - please wait ...")
        spinner.start()
        urls = get_series_links(url, myjson )
        spinner.stop()
    except:
        urls = get_links(url, myjson)
        spinner.stop()

    illegals = "*'%$!(),.:;"
    allseries = []
    for item in urls:
        series = item[0]
        allseries.append(series.replace('Series', ''))
        url    = item[1]
        url = url.strip('\n')
        episode = str(item[2])
        episode =  ''.join(c for c in episode if c.isprintable() and c not in illegals)
        insert_video(con, cur, series, episode, url)
    

    while True:
        query = f"SELECT COUNT(*) FROM 'videos'"
        cur.execute(query)
        result = cur.fetchone()
        row_count = result[0]
        unique_list = list(dict.fromkeys(allseries))
        if row_count <= ROW_COUNT:
            search = 99
            break
        print("[info] Series found are:-", end=' ')
        for item in unique_list:
            console.print(f"[pink1]{item}[/pink1]", end = ' ')
        console.print(f"[green]\nThere are over {ROW_COUNT} videos to display.\n\
        Enter the series number(s) to see a partial list,\n\
        or enter [pink1]'0'[/pink1] to show all episodes available[/green]\n\
        [red]Separate series numbers with a space \n[/red]")
        search = input("? ")
        if not re.match("^[0-9 ]+$", search):
            print ("Use only numbers and Spaces!")
        else:
            break

    if search == '0':
        cur.execute("SELECT * FROM videos")

    elif type(search) != int:
        srchlist = search.split(' ')
        partsql = "SELECT * FROM videos WHERE series='Series "
        for srch in srchlist:
            partsql = f"{partsql}{srch}' OR series='Series "
        partsql = partsql.rstrip(" OR series='Series ")
        sql = partsql + "';"
        cur.execute(sql)
        
    elif search == 99:
        cur.execute("SELECT * FROM videos")

    else:
        search = "Series " + search
        cur.execute("SELECT * FROM videos WHERE series=?", (search,))
    rows = cur.fetchall()
    # DannyBoi checker
    if len(rows)==0:
        print("[info] No series of that number found. Exiting. Check and try again. ")
        exit(0)
    con.close()
    beaupylist = []

    for col in rows:
        beaupylist.append(f"{col[1]} {col[2]} {col[3]}")
    spinner.stop()
    return beaupylist

def get_series_links(url, myjson):
    urllist = []
    tabs = len(myjson['props']['pageProps']['data']['tabs'])
    headers = {
            'Accept': '*/*',
            'Connection': 'keep-alive',
            'Origin': 'https://player.stv.tv',
            }
    for i in range(0, tabs-4):  
        series_guid = myjson['props']['pageProps']['data']['tabs'][i]['params']['query']['series.guid']
        response = client.get(f"https://player.api.stv.tv/v1/episodes?series.guid={series_guid}&limit=100&groupToken=0071", headers = headers)
        if response.status_code != 200:
            print(f"Error {response.status_code} on {url}")
            exit(0)
        mynextjson = json.loads(response.text)
        res = mynextjson['results']

        for i in range(0, len(res)):
            series = res[i]['playerSeries']['name']            
            episode = res[i]['playerSeries']['episodeIndex']
            data = [series, res[i]['_permalink'], episode]
            urllist.append(data) 
    return urllist

#single series
def get_links(url,  myjson):
    urllist = []
    data = myjson['props']['pageProps']['data']['tabs'][0]['data']
    for i in range(0, len(data)):
        title = data[i]['title']  # "Episode 1 of 2, Night One",
        urllist.append(["Series 1", f"https://player.stv.tv{data[i]['link']}", title])
    return urllist

def create_connection(): 
    con = None
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
    con.commit()
    return con, cur

def insert_video(con, cur, series, episode, url):
    #print(f"Inserting {series} {episode} {url}")
    sql = ''' INSERT INTO videos( series, episode, url) VALUES(?,?,?) '''
    cur.execute(sql, (series, episode, url))
    con.commit()

def keywordsearch(search):
    spinner = Spinner(DOTS, "Collecting data - please wait ...")
    spinner.start()
    client = Client()

    headers = {
        'Accept': '*/*',
        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Origin': 'https://player.stv.tv',
        'Referer': 'https://player.stv.tv/',
        'Host': 'search-api.swiftype.com',
        'Access-Control-Request-Method': 'POST',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    }
    #url = "https://search-api.swiftype.com/api/v1/public/engines/suggest.json"
    url = "https://search-api.swiftype.com/api/v1/public/engines/search.json"
    response = client.options(url, headers=headers)
    
    xdata = response.headers['x-request-id']
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Origin': 'https://player.stv.tv',
        'Referer': 'https://player.stv.tv/',
        'Host': 'search-api.swiftype.com',
        'Access-Control-Request-Method': 'POST',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
        'x-request-id': f'{xdata}'
    }
    json = {
        "engine_key": "S1jgssBHdk8ZtMWngK_y",
        "per_page": 100,
        "page": 1,
        
        "fetch_fields": {
        "page": [
            "title",
            "body",
            "resultDescriptionTx",
            "url"
        ]
        },
        "highlight_fields": {
        "page": {
            "title": {
            "size": 100,
            "fallback": True
            }
        }
        },
        "search_fields": {
        "page": [
            "title^3",
            "body",
            "category",
            "sections"
        ]
        },
        "q": search,
        "spelling": "strict"
    }    
    try:
        response =  client.post(url, headers= headers, json = json)
        mydict = response.json()
        if mydict['record_count']==0:
            spinner.stop()
            raise Exception
    except:
        return None

    beaupylist = []
    myrecd = mydict['records']['page']
    newcount= int(len(myrecd))
    urllist =[]
    for i in range (0, newcount): 
        title =  myrecd[i]['title'] 
        url =    myrecd[i]['url'] 
        if 'summary' not in url:  # some links are STV promotion/housekeeping
            continue 
        try:  
            desc  =  myrecd[i]['resultDescriptionTx']
        except:
            desc = 'No description found.'
        pass
        urllist.append(url)
        mystring = f"{i} {title}\n\t{desc}"
        beaupylist.append(mystring)
        
    spinner.stop()
    console.print(f"[green]🔺🔻 to scroll[/green]\n")
 

    link = select(beaupylist, cursor="🢧", cursor_style="cyan" , preprocessor = lambda val: prettify(val), page_size=PAGE_SIZE, pagination=True) 

    ind = link.split(' ')[0]
    return urllist[int(ind)]

def prettify(val):
    try:
        parts = val.split('\t')
        title = f"[green]{parts[0]}[/green]"  
        synopsis = f"[cyan]{parts[1]}[/cyan]"  
        return f"{title}\t{synopsis}"
    except:
        return f"[green]{val}[/green]"

def cleanup():
    ###############################################################################################
    # beaupy module that produces checkbox lists seems to clog and confuse my linux box's terminal; 
    # I do a reset after downloading.
    # if that is not what you want, as it may remove anyhttps://www.channel4.com/programmes/the-great-pottery-throw-down/on-demand/74089-004
    if os.name == 'posix':
        spinner = Spinner(CLOCK, "[info] Preparing to reset Terminal...")
        spinner.start()
        time.sleep(5)
        spinner.stop()     
        os.system('reset')
        
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

def dobrowse(url):
    resp = client.get(url)
    if resp.status_code != 200:
        raise Exception(f"Failed to fetch data from {url}")
    sel = Selector(text=resp.text)
    init_data = (sel.xpath('//*[@id="__NEXT_DATA__"]')).get()
    init_data = init_data.replace('<script id="__NEXT_DATA__" type="application/json">', '').replace('</script>', '')
    init_data = json.loads(init_data)
    #console.print_json(data=init_data)

    try:
        # Search for the nested episode data
        episode_data = jmespath.search("props.pageProps.data.assets", init_data)
        # convert wanted data into a list of dicts, with only the title, synopsis and link items
        res = jmespath.search("""
            [*].{
            title: title,
            synopsis: description
            link: link
            } """,  episode_data)
        #console.print_json(data=res)  
    
    except Exception as e:
        print(f"An error occurred while using jmespath to extract episode data: {e}")
    beaupylist = [] 

    for i in range (len(res)):
        beaupylist.append(f"{i} | {res[i]['title']} | \n\t{(res[i]['synopsis'])}")
    found = select(beaupylist, cursor="🢧", cursor_style="cyan" , preprocessor = lambda val: prettify(val),  page_size=PAGE_SIZE, pagination=True)
    f = found.split('|')[0]
    link  = res[int(f)]['link']
    link = f"https://player.stv.tv{link}"
    return(link)

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
        stv.run()
        # need a better entry point
        exit(0)
    elif 'Quit' in action:
        print("Exiting..")
        exit(0)
    else:
        return None
    
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
        if 'summary' in url:
            url = url.encode('utf-8', 'ignore').decode().strip()
            break
        else:
            print("A correct URL has 'summary' in the line")
    return url

def print_back(n=1, text='a'): 
    for _ in range(n): 
        sys.stdout.write(CURSOR_UP_ONE) 
        sys.stdout.write(ERASE_LINE)
    console.print(f"[bright_yellow]{text}[/bright_yellow]")



####################    main     ##############################
    # for testing
    #url = "https://player.stv.tv/summary/lionsgate-rosemarys-baby" # 1 series DRM
    #url = "https://player.stv.tv/summary/crime"  #  1 series no DRM
    #url = "https://player.stv.tv/summary/taggart" # multi series no DRM
    #url = "https://player.stv.tv/summary/motorbike-show"  # 3 series no DRM series # does not start at series 1
    #url = "https://player.stv.tv/summary/boris-becker-the-rise-and-fall/"
    #url = https://player.stv.tv/summary/banijay3-single-handed#banijay3-single-handed-series-2  # series 2 now found

if __name__ == '__main__':
    havedata = False
    urllist = None
    srchurl = None
    client = Client()
    
    title = PF.figlet_format(' S T V ', font='smslant')
    print(colored(title, 'green'))
    strapline = "An STV Video Search, Selector and Downloader.\n\n"
    print(colored(strapline, 'red'))
    con, cur = create_database()
    url = doactionselect()  
    beaupylist = get_next_data(url)          
    # check for single item in beaupylist and if so load directly
    if len(beaupylist) == 1:
        data = str(beaupylist[0]).split('https://')[1]
        stv.entrypoint(f"https://{data}")
        cleanup()
        exit(0)
    #console.print(f"[green]🔺🔻 to scroll[/green]\n")
    try:
        videos = select_multiple(beaupylist, minimal_count=1, page_size=PAGE_SIZE, pagination=True)
    except KeyboardInterrupt:
        cleanup()
        exit(0)
    
    for i in range(0, len(videos)):
        data = videos[i]
        #print(data)   
        result = re.search("https.*", data).group()
        result = result.rstrip("'")
        stv.entrypoint(str(result))
    gc.collect()

    cleanup()    
    exit(0)
