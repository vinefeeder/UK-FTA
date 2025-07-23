# A_n_g_e_l_a  20:09:2023
# script finds videos from a keyword search or direct URL entry.
# Greedy-search lists all series videos on request,
# waits for user selection before download
# uses an external downloader C4.py
# both chan4_loader.py and C4.py must be
# in the same folder.

import jmespath
from httpx import Client
from scrapy import Selector
import json, re, os
import sqlite3
from sqlite3 import Error
from beaupy import confirm, select, select_multiple
from beaupy.spinners import *
import time
import C4
import pyfiglet as PF
from rich.console import Console
from collections import OrderedDict
from rich.prompt import Prompt
import sys
from rich.prompt import Prompt

CURSOR_UP_ONE = "\033[F"
ERASE_LINE =  "\033[K"

BRIGHT_YELLOW = '\\033[93m'
BRIGHT_GREEN = '\\033[92m'

client = Client()
console = Console()

PAGE_SIZE = 12
ROW_COUNT = 12
optheaders = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'Access-Control-Request-Headers': 'x-correlation-id',
        'Access-Control-Request-Method': 'GET',
        'Connection': 'keep-alive',
        'Host': 'all4nav.channel4.com',
        'Origin': 'https://www.channel4.com',
        'Referer': 'https://www.channel4.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
    }
reqheaders={
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Host': 'all4nav.channel4.com',
            'Origin': 'https://www.channel4.com',
            'Referer': 'https://www.channel4.com/',
            'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',  
            'X-Correlation-Id': 'DOTCOM-d87a0aa3-197d-4e9b-bb05-054944eb9485',
        }
cookies = {
    '_abck': '91788E94B0137045BA67D94380348BD6~0~YAAQBoAQAsDiezKPAQAA47Z8XAuypLWBWxNe7qADoV+kPDISl3lnVXAzUk4JAsv7/zWAlgD6LQYWX6Sygzzn+AYvZyRSWwhlurO7LNoON4VATC7PiR08X2BuQ8lHznNusp17+U0p3E0SRbYMqwOCgcy+G/l1pnprAUtrCyzlwWrqqt69afJ/uf8XSs8qWhZREZ4NRRBD7zZ3cAUNTCo6gWNJV9DzmpFkVzo4NKDreIKUxri24qzryYF3Ys4GZHR9lEOAjtKOG9XyOY8J12XPqBAfyNJ+qSSbU1SI1mmiCSl8kNuTprdCexof3VsAEfQdmJzsesOGFgIVjnV97RlX4EYkB03jhXQVljtP6Vt8vS1AIfvT9V15wdJLRvU0Q3FjmRwGk9B3RRhMf/WmSzgp0FblRUMRdlSILiLsE6V7FQmYSDFHTIU=~-1~-1~-1',
    'bm_sz': 'D1622B61D9D83F4521B15A60DCCB6692~YAAQ5Y9lX447Hi6PAQAAZrb5XBeibEpru2t9d9kpUOJLcP44j4cqRIqjdeL8SzneP3uINMm/cA/tQZydA2C1KxeB0ySfWYLXWJpnjZyBq8YTaX6O4yL+yJqsUigAsUeZ5tJENdPGz2fZfGXAJ6G08GusJOZtpX3V73ZP9Z+3n68hNo8alXDLGJQ2sx9sKxuf1oRXuQs5rQMlat06McnwxXp0GUJlB9ohslFT2h8McVsbXo5QoUfErmSiZ+k03SJv/R771DJD7YuYr/lpbA46RTHo19Nlzy1Bnfgt7Y+52LA/OAtlg3ZpsjVMG15rA9jVoMR+Ur6QO/A63rnL08AcFdMEZKNpr0O1H4e1Wd9Kee7PGP6rX8I6lNkDlK7ThrVY/YrU7Zro66WSVTw/znye0URFUykz0oR2w+VcKNInu33QNUzXobPn/NXInPX7fAkFJolYz9PdC3gSGytpfc2rW5xiAKR3J9XqAOeCB7zzl2KPCYWaITLv3mbXtxKr5Xa0ATnuNDCZXJiUL32t3aCOn7JMf6MimU9/VA==~3360312~3159621',
    'AMCV_16B222CE527834FC0A490D4D%40AdobeOrg': '179643557%7CMCIDTS%7C19853%7CMCMID%7C60072622325236460448405604853795292779%7CMCAID%7CNONE%7CMCOPTOUT-1715259020s%7CNONE%7CvVersion%7C5.5.0',
    'AMCVS_16B222CE527834FC0A490D4D%40AdobeOrg': '1',
    'C4_AT': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3NUb2tlbiI6IlVHN3lGSnBFYzhxT2RZUXpLZFdrMGJRYWFCekwiLCJhY2Nlc3NUb2tlbkV4cGlyZXNBdCI6MTcxNTI1NDQyNjI2OCwiaWF0IjoxNzE1MjQzNjI3fQ.9xLi7Bry1mBGk8OmD29mAljKjtYbuiYNbiygtN9o1_A',
    'c4_mor_notification': 'false%3Btrue%3Btrue%3B125',
    'all4PreviousPageName': 'categories:documentaries:none:none:popular',
    'ak_bmsc': '8BC52DFD2F65160F95CBD4CE1F0B8AA4~000000000000000000000000000000~YAAQ5Y9lX407Hi6PAQAAZrb5XBfnJkgqaASWufU83O72inoYg2PMgvIdGnGZtHwJHbAu6Ycvj+I4j4DOyoxhRPoWKckbxoayAk/9A/l9D1ayxiYbUpmEKLAZ8wx4+H8MS2KJLuoJxiRcrHxkvGk+OQyswqgpaWRkji25HVdgm0d50NlaEfkGBg7ktapuI/S5zhegW4Kjkq+7tubh8dseoYcPlISz9Yc1HLkFYyR0hmRPdfCY2SA8FDNcW/bepd0ck7TLl20DMCoiOVAeUl+jCx+maoO6qtYS5GmhyqTgDLBvhXH3jgxEBHOY2d90zJ5YcoDJ0N9BuN9Qw5vZvkCOTmhPEU2YfJx2cSI4N75Y4hfdKEXtUiJIOjq1UNpGkiDweiEGeysU8PUygA+z',
    'bm_sv': '05649E6F7E3A7DD771A452AFCE1EEFF6~YAAQ5Y9lXzg9Hi6PAQAAzcT5XBfq1kDcEj0NEKKuEHJBXBJ26qDTD5mqvZZqapeBfMtX8uoaQf3sLh+4GJE47OayyYT7aAKZS3t03DnYPDr05A7DVK+WNyjObpdqlUG6zVR4YlbVEIxFa53GBbMvDErAGeArrPkM+JYUjO90Eik49lUf1dIeBFLbBIFRvqBoEYlUDGHPxFm1PjF7r0B8jZ0AmFEzoN3mkFPi9a6issJJLlNa7zJXW6V9wbQVxNh1ZTw=~1',
}

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-GB,en;q=0.5',
    'Referer': 'https://www.channel4.com/categories/boxsets',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
}

def create_connection(): 
  conn = None;
  try:
      conn = sqlite3.connect(':memory:')
  except Error as e:
      print(e)
  return conn


def get_next_data(url , title):
    global client
    spinner = Spinner(DOTS, "Collecting data - please wait ...")
    spinner.start()
    headers={
            'Host': 'www.channel4.com',
            'Referer': 'https://www.channel4.com/',
            'user-agent': 'Dalvik/2.9.8 (Linux; U; Android 9.9.2; ALE-L94 Build/NJHGGF)',
        }
    url = url.encode('utf-8', 'ignore').decode().strip()
   
    myhtml = client.get(url, headers=headers, follow_redirects=True).text
    sel = Selector(text = myhtml)
    selected = sel.xpath('/html/body/script[contains(text(), "__PARAMS__")]').extract()
    selected = selected[0]
    selected = selected[28:] #<script>windows.__PARAMS__ =
    selected = selected[:-9].replace('undefined', 'null') # parse issue
    myjson = json.loads(str(selected))
    #console.print_json(data = myjson)

    mytitles = jmespath.search('initialData.brand.episodes', myjson)
    res = jmespath.search("""
    [*].{
    episodeId: title,
    series: seriesNumber
    prog_id: programmeId                    
    magniurl: hrefLink                    
    } """,  mytitles)
    #print(res)
    ## prepare sql
    con = create_connection()
    cur = con.cursor()

    sql = '''
    CREATE TABLE IF NOT EXISTS videos(
    rowid INTEGER PRIMARY KEY AUTOINCREMENT,
    series INTEGER,
    episode VARCHAR,
    url VARCHAR,
    UNIQUE (url) 
    );
    '''
    cur.execute(sql)

    i = 1 # rowid
    rowid = 0
    allseries = []
    for i in range(0, len(res)):
        url = f"https://www.channel4.com{res[i]['magniurl']}"
        if 'None' in url:
            continue
        episode = res[i]['episodeId'].replace('Episode','') # Episode n -> n
        series = int(res[i]['series']) # n
        episode = rinse(episode)
        if not series:
            series = 0
        
        allseries.append(series)
        rowid += i
        sql = f''' INSERT OR IGNORE INTO videos(rowid, series, episode, url) VALUES('{rowid}','{series}','{episode}','{url}');'''
        cur.execute(sql)
    spinner.stop()

    while True:
        if i <= ROW_COUNT: 
            search = '0'  
            break
        d = dict.fromkeys(allseries)
        myseries = OrderedDict(sorted(d.items(), key=lambda t: t[0]))
        unique_list = list(myseries)
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
        cur.execute("SELECT * FROM videos order by series")

    elif type(search) != int:
        srchlist = search.split(' ')
        partsql = "SELECT * FROM videos WHERE series='"
        for srch in srchlist:
            partsql = f"{partsql}{srch}' OR series='"
        partsql = partsql.rstrip(" OR series='")
        sql = f"{partsql}'  order by series;"
        cur.execute(sql)

    else:
        search = "Series " + search
        cur.execute("SELECT * FROM videos WHERE series=? order by series", (search))
    rows = cur.fetchall()
    
    if len(rows)==0:
        print("[info] No series of that number found. Exiting. Check and try again. ")
    con.close()
    beaupylist = []
    index = [] 
    inx = 0
    for col in rows:
        beaupylist.append(f"{col[1]} {col[2]} {col[3]}")
        index.append(inx)
        inx+=1
    # 
    if len(beaupylist) == 1:
        print_back(2, "Only one video found. Loading directly...")
        for col in rows:
            url = col[3]
        C4.main(url)
        exit(0)
        
    return index, beaupylist 

def rinseurl(string):
    illegals = "*'%$!(),;"  # safe for urls
    string = ''.join(c for c in string if c.isprintable() and c not in illegals)
    string = string.lstrip(' ')
    return string

def rinse(string):
    illegals = "*'%$!(),;"  # safe for urls
    string = ''.join(c for c in string if c.isprintable() and c not in illegals)
    return string

def keywordsearch(search):
    print("searching", end=' ')
    spinner = Spinner(DOTS)
    spinner.start() 
    client = Client() 
    optheaders = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'Access-Control-Request-Headers': 'x-correlation-id',
        'Access-Control-Request-Method': 'GET',
        'Connection': 'keep-alive',
        'Host': 'all4nav.channel4.com',
        'Origin': 'https://www.channel4.com',
        'Referer': 'https://www.channel4.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
    }
    reqheaders={
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Host': 'all4nav.channel4.com',
            'Origin': 'https://www.channel4.com',
            'Referer': 'https://www.channel4.com/',
            'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',  
            'X-Correlation-Id': 'DOTCOM-d87a0aa3-197d-4e9b-bb05-054944eb9485',
        }
    url = f"https://all4nav.channel4.com/v1/api/search?expand=default&q={search}&limit=100&offset=0"
    try:
        client.get('https://www.channel4.com')
        client.options(url , headers = optheaders)
        response = client.get(url, headers = reqheaders)
        myjson = response.json()  
        #console.print_json(data=myjson)
        #if myjson['results']['title']=='No Matches':
        #    raise Exception
    except:
        spinner.stop()
        return None
    res = jmespath.search("""
    results[*].brand.{
    url: href,
    title: websafeTitle,
    synopsis: description
    } """,  myjson)

    beaupylist = []
    try:
        for i in range(0 ,len(res)):
            title = res[i]['title']
            url = res[i]['url']
            synopsis = res[i]['synopsis']
            strtuple = (f"{i} {title}\n\t{synopsis}")
            beaupylist.append(strtuple)
    except:
        print(f"Nothing was found for your search term {search}\nExiting....")
        spinner.stop()
        cleanup()
        exit(0)
    spinner.stop()
    found = select(beaupylist,   preprocessor = lambda val: prettify(val), cursor="🢧", cursor_style="pink1", page_size=PAGE_SIZE, pagination=True)
    ind = found.split(' ')[0] 
    return res[int(ind)]['url']

def doactionselect():
    # top level choice for action
    fn = [
        "[green]Search by Keyword(s)",
        "Greedy Search by URL",
        'Browse by Category[/]',
        '[red]Download by URL[/red]',
        '[yellow]Quit[/]'
        ]
    action = select(fn, cursor="🢧", cursor_style="pink1")
    if 'Keyword(s)' in action:
        return dosearch()
    elif 'Greedy' in action:
        return dourlentry()
    elif 'Browse' in action:
        return dobrowseselect()
    elif 'Download' in action:
        print_back(12,'') ## clear unwanted sceen text
        C4.run()
        exit(0)
    elif 'Quit' in action:
        cleanup()
        exit(0)
        
        
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
    url = Prompt.ask("[red]Enter URL: [/red]")
    return url

def dobrowseselect():
    # 2nd level action choice
    # provide list of categories to browse
    # calls dobrowse(url)
    global media_dict
    fn = []
    for key in media_dict.keys():
        fn.append(key)
        
    action = select(fn, preprocessor=lambda val: f"[green]{val}[/]", cursor="🢧", cursor_style="pink1")
    browse_url = media_dict[action]
    url = dobrowse(browse_url)
    return url

def dobrowse(browse_url):
    # browse option create list of video  directly linked, and follow collection of videos to gather more.
    beaupylist = []
    try:
        req = client.get(browse_url, headers = headers, cookies=cookies)

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
        #console.print_json(data=init_data)
        #object►initialData►brands►items►0►hrefLink
        myjson = init_data['initialData']['brands']['items']
        res = jmespath.search("""
        [*].{
        href: hrefLink
        label: labelText
        overlaytext: overlayText            

        } """,  myjson)
        
        #print(res)
        for i in range (len(res)):
            #href = res[i]['href'].split('?')[0]
            label = res[i]['label']
            overlaytext = res[i]['overlaytext']
            beaupylist.append(f"{i} {label}\n\t{overlaytext}")
    except Exception as e:
        print(e)
        cleanup()
        exit(1)
    
    found = select(beaupylist,  preprocessor=lambda val: prettify(val), cursor="🢧", cursor_style="pink1",  page_size=PAGE_SIZE, pagination=True)  
    ind = found.split(' ')[0]
    url = res[int(ind)]['href']
    return url

def prettify(val):
    
    try:
        parts = val.split('\t') 
        title = f"[green]{parts[0]}[/green]"  
        synopsis = f"[cyan]{parts[1]}[/cyan]"  
        return f"{title}\t{synopsis}"
    except:
        return f"[green]{val}[/green]"

def cleanup():
    ##############################################################################################
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

#################  main  ===============
if __name__ == '__main__':
    title = PF.figlet_format(' A L L 4 ', font='smslant')
    strapline = "An All4 Video Search, Selector and Downloader.\n\n"
    console.print(f"[green]{title}[/]")
    console.print(f"[red]{strapline}[/red]\n\n[green]🔺🔻 to scroll[/green]\n")
    client = Client()
    
    media_dict = {
        'Film': 'https://www.channel4.com/categories/film',
        'Documentary': 'https://www.channel4.com/categories/documentaries',
        'Comedy': 'https://www.channel4.com/categories/comedy',
        'Drama': 'https://www.channel4.com/categories/drama',
        'Entertainment': 'https://www.channel4.com/categories/entertainment',
        'Lifestyle': 'https://www.channel4.com/categories/lifestyle',
        'News & Current Affairs': 'https://www.channel4.com/categories/news-current-affairs-and-politics',
        'Sport': 'https://www.channel4.com/categories/sport',
        'World Drama': 'https://www.channel4.com/categories/world-drama',
        'Box Sets': 'https://www.channel4.com/categories/boxsets', 
    }
    
    url = doactionselect()
    print(url)
    index, beaupylist = get_next_data(url ,None)
    links = select_multiple(beaupylist,   preprocessor=lambda val: (f"[green]{val}[/green]"), minimal_count=1, page_size=PAGE_SIZE, pagination=True)
    for item in links: 
        parts = item.split(' ')
        url = parts.pop()
        myAll4 = C4.main(url)
    

        
    


