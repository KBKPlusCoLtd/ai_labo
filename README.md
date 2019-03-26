# ai_labo

必要なもの
・Python
・Django
・Numpy
・Chainer
・ChainerRL


Python
検索してexeからinstallする
installするときに環境変数PATHに設定するにチェックを入れる
チェックしていないとpip installができない


Django
Numpy
Chainer
ChainerRL
Pythonのライブラリ
Pythonをinstallした後pipコマンドでinstallできる
コマンドプロンプトを開いて以下コマンドを実行
pip install django
pip install numpy
pip install chainer
pip install chainnerrl


installが終わったらコマンドプロンプトからai直下で以下コマンドでDjangoサーバーを起動
python manage.py runserver

起動が完了したら以下URLをブラウザで開く
http://localhost:8000/app

static/ai下にそれぞれの盤面の学習データを格納している
train.pyを以下コマンドで実行することで学習データの作成ができる
python train.py
