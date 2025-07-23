# A_n_g_e_l_a

import time
from httpx import Client
import requests
import time
import json
client = Client()

class Sethmackey:
    def __init__(self):
        file = r'ukfta/my5_dl/config.py'
        # Thanks stabbedbybrick for hosting this
        res = requests.get(f"https://gist.githubusercontent.com/stabbedbybrick/8726c719721eac50a28f7bc3c94f18e9/raw/s.txt")
        res = json.loads(res.text)

        hmac = f'''HMAC_SECRET = "{res['hmac']}"'''
        aes = f'''AES_KEY = "{res['key']}"'''
        time_stamp = int(time.time_ns() // 1_000_000_000)

        # replacements to make
        text1 = f'{hmac}\n'
        text2 = f'{aes}\n'
        text3 = f"{time_stamp}\n"
    

        # replace_line(<path to your file> , <line number to change> < text to insert>)
        # line numbers in text count from 0
        self.replace_line(file, 1 , text1)
        self.replace_line(file, 2 , text2)
        self.replace_line(file, 3 , text3)
        return
    
    def replace_line(self,file_name, line_num, text):
        lines = open(file_name, 'r').readlines()
        lines[line_num] = text
        out = open(file_name, 'w')
        out.writelines(lines)
        out.close()
        return

if __name__ == '__main__':
    Sethmackey()    
