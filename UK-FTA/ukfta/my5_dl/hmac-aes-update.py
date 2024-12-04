# A_n_g_e_l_a
# revision May 2024


# 
# this script runs a headless version of firefox to run Diazole's retrieve-keys.html, local - on your system.
# it then updates the config.py in my5-dl-main/
# You should not  need a firefox binary file - geckodriver - it should be installed with Selenium
# but see https://github.com/mozilla/geckodriver/releases should you need to download it.

# pip install selenium   - is optional so long as the autohmac target URL is working.
#



from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import time
import json

import pathlib
mypath = (pathlib.Path(__file__).parent.resolve())


LOCATION_RETRIEVE_KEYS_HTML = rf"file:///{mypath}/keys/retrieve-keys.html"
##  end edit - ONE MORE BELOW

def replace_line(file_name, line_num, text):
    lines = open(file_name, 'r').readlines()
    lines[line_num] = text
    out = open(file_name, '+w')
    out.writelines(lines)
    out.close()

options = Options()
options.add_argument('-headless')
driver = webdriver.Firefox(options=options)

driver.get(f"{LOCATION_RETRIEVE_KEYS_HTML}")
time.sleep(3) # do not remove this! Edit seconds to wait upwards if you get 'None' reported.
source = driver.page_source
result = source.replace('<html><head></head><body>','').replace('</body></html>','')
mydict = json.loads(result)
driver.close()

hmac = f'''HMAC_SECRET = "{mydict['HMAC_SECRET']}"'''
aes = f'''AES_KEY = "{mydict['AES_KEY']}"'''


file = rf'{mypath}/config.py'

text1 = f'{hmac}\n'
text2 = f'{aes}\n'

replace_line(file, 1 , text1)
replace_line(file, 2 , text2)
print(f"\nAll done!\n\n{text1}{text2}\nsuccessfully replaced into {file}")

