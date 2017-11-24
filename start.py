import os, sys, json

with open('config.json') as f:
    ver = json.load(f).get('VERSION')

## STARTS TUXEDO ##
# PM2 has failed me. 

print(f'## Tuxedo ##\nversion {ver}\nBy ry00001 (ry00001#3487), HexadecimalPython (Hexadecimal™#0910) and Devoxin (Devoxin#0387).\nThis is free and open-source software.')

while True:
    os.system(f'{sys.executable} bot.py')
    print('Bot crashed! Rebooting...')