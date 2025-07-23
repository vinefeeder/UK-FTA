# A_n_g_e_l_a  July 2024

# script finds videos from browsing, a keyword search or direct URL entry.
# Greedy-search lists all series-videos on request,
# waits for user selection before download
# Script uses an external downloader ITVX.py which also is a stand-alone single itvx downloader.
# Both itv_loader.py and ITVX.py must be
# in the same folder.
# ITVX.py works as a stand-alone if provided with a valid url

# see line 437 to add more search categories from itv

import jmespath
from httpx import Client
import httpx
from scrapy import Selector
import json, re, os, sys
import sqlite3
from sqlite3 import Error
from beaupy import confirm, select, select_multiple
from beaupy.spinners import *
import time
import ITVX as itv
import pyfiglet as PF
from rich.console import Console
from rich.prompt import Prompt

CURSOR_UP_ONE = "\033[F"
ERASE_LINE =  "\033[K"

BRIGHT_YELLOW = '\\033[93m'
BRIGHT_GREEN = '\\033[92m'

client = Client()
console = Console()
SEARCHTERM = ''
beaupylist = []

PAGE_SIZE = 12
ROW_COUNT = 12

headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-GB,en;q=0.5',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Cookie': '_abck=A1A08255FE99C45CAC8BB39DC002463A~-1~YAAQlsNQaNgSF8+OAQAAOjpjGQsKtQ21d/7RTffmcYCpKrErWVEYe5M6nx/ug1GIBEuxlX9YcLj+Qjxe20XuToMMEU728OFeN/sGOT6CoVXQ5ol8WVjtQ13p7125ZFk3M0VC6paFGKeb/r6Qel1Y9KvHP4HBgjLKfXPESFZNoXpdmu1b0KHXPhQyYukJj6rB4ymRL/eHG6GaRllBoPrbI9ph6BQyT08uy972CrSqDUwDYzGyXUfny2XWV/5+IYaKQp51x3W7cWV2FlUdKMGvCjVDBSQ5jod+DY+egata67ec6jXb6RBN5YxOxEVOoSOluwjO0+jq3mzXL4YdqULRE35H6h3WgFSRj4qbnaIQei/ea4/Hmu2Qc957nMdNtiikhX8gLBhbUI3jkVGXWDFIYUVdVg==~-1~-1~-1; bm_sz=F6B3B11BFA71C7D1547DF3B6B5ECA5AA~YAAQlsNQaM4SF8+OAQAA3jljGRficGYfRHfTPf8aevaWNA0t/sOAYABByhUS53Dn2r3sAD+KuGzOpch9KLD9UTysl1B4qcr6XB2uV+lDQc99MGI45IwBPhKBFTaCVpLq0HZ/1moyvwVCQYUmeVfQHIQvXbj/Wb0pKRwKnH6cyWTtTXFUCFybwcJK9bcn7h7BQB3zvGednWSpl8wSCLnq5ImF5x1UolAxlwpbEdE+zzi4EXM4lqrz5D8qYBJx/0yon+0zOMH/W8tr59VuzjLLl7mvbpE5MQdyHnUicxbNjeeDXctwqYwFnNpDKPyr4JZrvVRkBX/rCEy+GYK3FJkeXSMuxnjoI2PTvirrBZis+wWpmHPK60GbwnrpVRpN/cZcrd8p5glRwCSk~3359300~3228998; accept-cookies=accepted; Itv.Cid=bb88e776-5cf0-4162-ad6c-401cbc27c057; Itv.Session={"tokens":{},"sticky":false,"redirect":"/watch/collections/make-it-a-movie-night/2CIASIVXkb4A6R1XxJ4s1f"}; _sp_id.74e0=486749f3-a756-4837-b98f-8c7142099040.1714117885.3.1714130667.1714122413.387dbc76-672c-4911-bc99-301f39dceb7e.f43b24ed-5128-4140-96ca-dab13ddb75ea.044437e0-b16d-44fc-823a-5d9a255a491e.1714130017273.3; _sp_ses.74e0=*',
    }

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
        print_back(7,'') ## clear unwanted sceen text
        myITV= itv.ITV()
        myITV.run()
        cleanup()
        exit(0)
    elif 'Quit' in action:
        cleanup()
        exit(0)
        
def parse_collection_url(collection_url):
    global headers
    response = client.get(collection_url, headers=headers, follow_redirects=True)
    sel = Selector(text=response.text)
    videos = sel.xpath("/html/body/div/div/div/main/div/section/div/a[*]").extract()
    videos_info = []
    for video in videos:
        sel = Selector(text=video)
        synopsis = sel.xpath('//article/@aria-label').extract()[0]
        url = f"https://www.itv.com{sel.xpath('//a/@href').extract()[0]}"
        videos_info.append({"synopsis": synopsis, "url": url})
    return videos_info

def dobrowse(browse_url):
    # browse option create list of video  directly linked, and follow collection of videos to gather more.
    beaupylist = []
    global headers
    response = client.get(browse_url, headers=headers, follow_redirects=True)
    response.raise_for_status()
    sel = Selector(text=response.text)
    selected = sel.xpath("/html/body/div/div/div/main/div/section/div/a[*]").extract()

    for html in selected:
        sel = Selector(text=html)
        synopsis = sel.xpath('//article/@aria-label').extract()[0]
        url = f"https://www.itv.com{sel.xpath('//a/@href').extract()[0]}"
        if 'collection' in url:
            # parse collection URL for more video urls
            videos_info = parse_collection_url(url)
            for video_info in videos_info:
                beaupylist.append(f"{video_info['synopsis']}\n\t{video_info['url']}")
        else:
            beaupylist.append(f"{synopsis}\n\t{url}")

    found = select(beaupylist,  preprocessor=lambda val: (f"[green]{val}[/green]"), cursor="🢧", cursor_style="cyan",  page_size=PAGE_SIZE, pagination=True)  
    url = found.split('\n\t')[1]
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
        
    url = keywordsearch(search)
    return url

def dobrowseselect():

    # 2nd level action choice
    # provide list of categories to browse
    # calls dobrowse(url)
    fn = []
    for key in media_dict.keys():
        fn.append(key)
        
    action = select(fn, cursor="🢧",  cursor_style="cyan", preprocessor= lambda val: (f"[green]{val}[/green]"), page_size=PAGE_SIZE, pagination=True) 
    browse_url = media_dict[action]
    url = dobrowse(browse_url)
    return url
    
    
def dourlentry():
    # 2nd level action Enter URL
    url = Prompt.ask("[red]Enter URL: [/red]")
    return url
    
##########################
def get_next_data(url):
    global client

    headers={
            'authority': 'www.itv.com',
            'user-agent': 'Dalvik/2.9.8 (Linux; U; Android 9.9.2; ALE-L94 Build/NJHGGF)',
        }
    try:
        r = client.get(url, headers=headers, follow_redirects=True)
        if r.status_code == httpx.codes.ok:
            myhtml = r.text
        else:
            print("The response did not indicate success; try again." )
            exit(0)
    except:
        print("The search yielded no results; try again." )
        exit()
        
    spinner = Spinner(DOTS, "Collecting data - please wait ...")
    spinner.start()
    sel = Selector(text = myhtml)
    selected = sel.xpath('//*[@id="__NEXT_DATA__"]').extract()
    selected = selected[0] 
    pattern = r'\s*({.*})\s*' 
    myjson = json.loads(re.search(pattern, selected).group())
    mytitles = jmespath.search('props.pageProps', myjson)
    res = jmespath.search("""
    seriesList[].titles[].{
    episode: episode
    eptitle: episodeTitle
    series: series            
    magniurl: playlistUrl
    description: description
    episodeId: episodeId
    letterA: encodedEpisodeId.letterA
    contentInfo: contentInfo
    channel: channel

    } """,  mytitles)
    #console.print_json(data = myjson)
    #exit(0)
    fix = jmespath.search("""
    query.{
    programmeSlug: programmeSlug
    programmeId: programmeId                                               
    }""",myjson)
    programmeSlug = fix['programmeSlug']
    programmeId = fix['programmeId']
    ## prepare sql
    con = create_connection()
    cur = con.cursor()

    sql = '''
    CREATE TABLE IF NOT EXISTS videos(
    rowid INTEGER PRIMARY KEY AUTOINCREMENT,
    series VARCHAR,
    episode VARCHAR,
    eptitle VARCHAR,
    url VARCHAR,
    magniurl VARCHAR,
    UNIQUE (url) 
    );
    '''
    cur.execute(sql)
    
    i = 1 # rowid
    rowid = 0
    allseries = []
    for i in range(0, len(res)):
        magniurl = res[i]['magniurl']
        info = res[i]['contentInfo']
        info = specialrinse(info)  # SQL: remove apostrophe to prevent SQL exec parse errors
        letterA = res[i]['letterA']
        series = res[i]['series']
        episode =res[i]['episode']
        eptitle = res[i]['eptitle']
        
        if series == 'null':   
            series = 99
        allseries.append(series)
        
        if episode == 'null':
            episode = info
        if not type(series)==int:
            series= 99  # others,  specials, null-entry
            
        url = f"https://www.itv.com/watch/{programmeSlug}/{programmeId}/{letterA}"
        url =  rinse(url)
        rowid += i
        if eptitle:
            eptitle = rinse(eptitle)
        else:
            eptitle = res[i]['description'] 
            eptitle = rinse(eptitle) 
        sql = f''' INSERT OR IGNORE INTO videos(rowid, series, episode, eptitle, url, magniurl) VALUES('{rowid}','{series}','{episode}','{eptitle}','{url}','{magniurl}');'''
        cur.execute(sql)
    
    #print(allseries)
    sortedseries = custom_sort_and_remove_duplicates(allseries)
    
    spinner.stop()
    global SEARCHTERM
    while True:
        if i <= ROW_COUNT: 
            search = '0'  
            break
        unique_list = sortedseries
        print_back(2, f"A search {SEARCHTERM}\nfound series:-")
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
        console.print("[red][info] No series of that number found. Exiting. Check and try again. [/red]")
    con.close()
    beaupylist = []
    urllist = [] 

    for col in rows:  
        #                             series   episode  eptitle                                url
        beaupylist.append(f"{col[1]} {col[2]} {col[3].replace(' ','-').lstrip('-')}") #\n\t{col[4]}")
        urllist.append(col[4])
        
    return urllist, beaupylist 

def custom_sort_and_remove_duplicates(lst):
    # Replace non-integer elements  [eg special, others] with 99
    modified_list = [x if isinstance(x, int) else 99 for x in lst]
    sorted_unique_list = sorted(set(modified_list), key=modified_list.index)
    return sorted_unique_list

def create_connection(): 
    conn = None
    try:
        conn = sqlite3.connect(':memory:')
    except Error as e:
        print(e)
    return conn

def rinse(string):
    illegals = "*'%$!(),;"  
    string = ''.join(c for c in string if c.isprintable() and c not in illegals)
    return string

def keywordsearch(search):
    global SEARCHTERM
    search = search.title()
    SEARCHTERM = f"for {search}"
    print("searching", end=' ')
    spinner = Spinner(DOTS)
    spinner.start()  
    #client = Client(
    headers={
            'authority': 'www.itv.com',
            'user-agent': 'Dalvik/2.9.8 (Linux; U; Android 9.9.2; ALE-L94 Build/NJHGGF)',
            'Referer': 'https://www.itv.com/',
        }
    
    #url = f"https://textsearch.prd.oasvc.itv.com/search?broadcaster=itv&featureSet=clearkey,outband-webvtt,hls,aes,playready,widevine,fairplay,bbts,progressive,hd,rtmpe&onlyFree=true&platform=dotcom&query={search}"
    url = f"https://textsearch.prd.oasvc.itv.com/search?broadcaster=itv&channelType=simulcast&featureSet=clearkey,outband-webvtt,hls,aes,playready,widevine,fairplay,bbts,progressive,hd,rtmpe&onlyFree=true&platform=dotcom&query={search}&size=24"
    try:
        response = client.get(url, headers=headers, follow_redirects=True)
        if response.status_code == 200:
            pass
        else:
            print(f"Response gave an error {response.status_code} \n {response.content}")
            sys.exit(0)
        myjson = response.json()
    except:
        spinner.stop()
        print("The response to that search was not a success; try again")
        exit(0) 
    res = jmespath.search("""
    results[?data.tier=='FREE'].{
    api1: data.legacyId.officialFormat,
    title: data.[programmeTitle, filmTitle, specialTitle],
    synopsis: data.synopsis
    } """,  myjson)
 
    beaupylist = []
    saved = []
    for item in res:
        api1 = item['api1'].replace('/', 'a')
        title = next((value for value in item['title'] if value is not None), '')
        title = title.replace(' ', '-')
        url = f"https://www.itv.com/watch/{title}/{api1}"
        url = rinseurl(url)
        synopsis = item['synopsis']
        beaupylist.append(f"{len(beaupylist)} {title}\n\t{synopsis}")
        saved.append(url)
    spinner.stop()
    found = select(beaupylist,  preprocessor=lambda val: prettify(val), cursor="🢧", cursor_style="pink1",  page_size=PAGE_SIZE, pagination=True)
    if not found:
        print("Nothing was found for that search word: try again")
        exit(0)
        
    ind = found.split(' ')[0]
    url = saved[int(ind)]
    #print(url)
    return url

def rinseurl(string):
    illegals = "*'%$!(),;"  # safe for urls
    string = ''.join(c for c in string if c.isprintable() and c not in illegals)
    string = string.lstrip(' ')
    return string

def specialrinse(string):
    illegals = "'"  # for SQL:  apostophes kill SQL exec
    string = ''.join(c for c in string if c.isprintable() and c not in illegals)
    string = string.lstrip(' ')
    return string

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
        
def print_back(n=1, text='a'): 
    for _ in range(n): 
        sys.stdout.write(CURSOR_UP_ONE) 
        sys.stdout.write(ERASE_LINE)
    console.print(f"[bright_yellow]{text}[/bright_yellow]") 
    
def prettify(val):
    try:
        parts = val.split('\t') 
        title = f"[green]{parts[0]}[/green]"  
        synopsis = f"[cyan]{parts[1]}[/cyan]"  
        return f"{title}\t{synopsis}"
    except:
        return f"[green]{val}[/green]"


#################  main  ===============
#os.system(r"setterm  -background black -foreground  yellow -store ")

if __name__ == '__main__':
    title = PF.figlet_format(' I T V X ', font='smslant')
    console.print(f"[green]{title}[/]")
    strapline = "An ITVX Video Search, Selector and Downloader.\n\n"
    console.print(f"[red]{strapline}[/red]\n\n[green]🔺🔻 to scroll[/green]\n")
    
    ##############################################################################################
    #                                                                                            #
    ###  you can add to these if your category of browse programmes are not in this section    ###
    #                                                                                            #
    ##############################################################################################
    media_dict = {
        'Films': "https://www.itv.com/watch/collections/make-it-a-movie-night/2CIASIVXkb4A6R1XxJ4s1f",
        'Drama - Top Picks': "https://www.itv.com/watch/collections/top-picks/51Ry6KaT5pg9HYDJ8AqPwk", 
        'Drama - Gritty Thrillers': "https://www.itv.com/watch/collections/gritty-thrillers/5lTuwNT5hAkUyQJdPabiGT",
        'Drama - True Life': "https://www.itv.com/watch/collections/true-life-drama/1nYAN4ipGU6L0qmgimh1lE",
        'Drama - fresh in': "https://www.itv.com/watch/collections/fresh-in/7K0pfBiDFvOdBeHr7SnDzo",
        'Drama - Watching The Detectives': "https://www.itv.com/watch/collections/watching-the-detectives/6nn4AfQEAlnndtiI9i2Yaw",
        'Drama - Comedy Drama': "https://www.itv.com/watch/collections/comedy-drama/5lADfSZ7PP5dNeJ6BCW5Gb",
        'Comedy': "https://www.itv.com/watch/collections/show-me-the-funny/33idcDIeV32Cd3V7czYDeP", 
        'Entertainment & Reality': "https://www.itv.com/watch/collections/top-picks/4qcfuXnvuom6zss67k7e6p",
        'Sport - Football': "https://www.itv.com/watch/collections/football/6iS0VOrNqLWQNCLL5T0nxL",
        'Sport - Top Picks': "https://www.itv.com/watch/collections/top-picks/4CwpvlYDmVs0jumu0tA0Iu",
        'Sport - Fresh In': "https://www.itv.com/watch/collections/fresh-in/2h7nZMeKipItXfeVcGCGlo",
        'Unmissable - Boxsets': "https://www.itv.com/watch/collections/unmissable-boxsets/5vk4Kkk8zRTiG3cWI698fR",
        'Kids - Top Picks': "https://www.itv.com/watch/collections/kids-top-picks/4ZSxLvMbULBxNbA9AqY96R",
        'Kids - Just Added': "https://www.itv.com/watch/collections/just-added/5V2KreUaz10YZevYEN6R3c",
    
    }
    myITV =  itv.ITV()
    url = doactionselect()
    urllist, beaupylist = get_next_data(url)


    links = select_multiple(beaupylist, preprocessor=lambda val: prettify(val), minimal_count=1, page_size=PAGE_SIZE, pagination=True)
    print_back(8, '')  # clear  unwanted sceen text
    # Create a dictionary to map descriptions to URLs
    url_map = {beaupylist[i]: urllist[i] for i in range(len(beaupylist))}
    for link in links:
        url = url_map[link]
        myITV.download(url, 'No')
    cleanup()
    