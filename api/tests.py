from django.test import TestCase

# Create your tests here.
import requests
import json


url = "http://127.0.0.1:8000/api/"
sess = requests.session()

print(sess.get(url))

csrftoken = sess.cookies['csrftoken']

# ヘッダ
headers = {'Content-type': 'application/json',  "X-CSRFToken": csrftoken}

# 送信データ
prm = {"board":[
0,1,1,1,
2,1,2,2,
1,2,2,2,
1,2,2,2],"player_place":[0,2],"level":"1",
"turn":1,"board_size":4}

# JSON変換
params = json.dumps(prm)

# POST送信
res = sess.post(url, data=params, headers=headers)

# 戻り値を表示
print(json.loads(res.text))
