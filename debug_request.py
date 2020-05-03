#debugging script

import requests

TOKEN = "905448495:AAEtrGrGOKCHazkQ5SbpUMNi5OCjdiKRypQ"
MAIN_URL = "https://api.telegram.org/bot{}".format(TOKEN)

#catching group_id
up = requests.get("{}/getUpdates".format(MAIN_URL))
print(up)
a = up.text.split(',')
for i in a:
  print (i)