import os, sys, json

with open('config.json') as f:
    ver = json.load(f).get('VERSION')

## STARTS TUXEDO ##
# PM2 has failed me. 

while True:
    os.system(f'{sys.executable} bot.py')
    print('Bot crashed! Rebooting...')