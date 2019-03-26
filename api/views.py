from django.shortcuts import render
from django.http.response import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from collections import OrderedDict
from django.core import serializers
import json
import numpy as np
import sys
import re # 正規表現
import copy
import os
import chainer
import chainer.functions as F
import chainer.links as L
import chainerrl
import numpy as np
import random
from api.board import Board

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLACK = 1  # ボードのある座標にある石：黒
WHITE = 2  # ボードのある座標にある石：白
# -*- coding: utf-8 -*-
"""
リバーシプログラム（盤面8x8）：人間と対戦用プログラム（DNN，DQNを利用）
Copyright(c) 2018 Koji Makino and Hiromitsu Nishizaki All Rights Reserved.
"""
#### Q関数の定義 ###
class QFunction(chainer.Chain):
    def __init__(self, obs_size, n_actions, n_nodes):
        w = chainer.initializers.HeNormal(scale=1.0) # 重みの初期化
        super(QFunction, self).__init__()
        with self.init_scope():
            self.l1 = L.Linear(obs_size, n_nodes, initialW=w)
            self.l2 = L.Linear(n_nodes, n_nodes, initialW=w)
            self.l3 = L.Linear(n_nodes, n_nodes, initialW=w)
            self.l4 = L.Linear(n_nodes, n_actions, initialW=w)

    # フォワード処理
    def __call__(self, x):
        h = F.relu(self.l1(x))
        h = F.relu(self.l2(h))
        h = F.relu(self.l3(h))
        return chainerrl.action_value.DiscreteActionValue(self.l4(h))

@ensure_csrf_cookie
def index(request):
    # ---------------ここからRequestの取得-----------------
    # リクエストから値を取得
    # getの場合、空で返却 tests.pyでcsrftoken取得用
    if request.method == 'GET':
        return JsonResponse({})

    # jsonを受け取る
    print('----request----')
    print(request.body)
    datas = json.loads(request.body)
    size = int(datas['board_size'])
    you = int(datas['turn'])
    place = datas['player_place']

    if size == 8:
        level = int(datas['level']) * 5000 # 8x8の場合のみ
    else:
        level = int(datas['level']) * 1000
    # ---------------ここまでRequestの取得-----------------

    # boardの設定
    board = Board(size) # ボードの初期化
    board.board[0:size * size - 1] = np.reshape(datas['board'], (size, size)) # 1次元配列をsize x sizeの2次元配列に変換

    # ---------------ここからAiの設定-----------------
    obs_size = size * size # ボードサイズ（DNN入力次元数）
    n_actions = size * size # 行動数はsize*size（=ボードのどこに石を置くか）
    n_nodes = 256 # 中間層のノード数
    q_func = QFunction(obs_size, n_actions, n_nodes)

    # optimizerの設定
    optimizer = chainer.optimizers.Adam(eps=1e-2)
    optimizer.setup(q_func)
    # 減衰率
    gamma = 0.99
    # ε-greedy法
    explorer = chainerrl.explorers.LinearDecayEpsilonGreedy(
        start_epsilon=1.0, end_epsilon=0.1, decay_steps=50000, random_action_func=board.random_action)
    # Expericence Replay用のバッファ（十分大きく）
    replay_buffer = chainerrl.replay_buffer.ReplayBuffer(capacity=10 ** 6)
    # エージェント．DQNを利用．
    agent = chainerrl.agents.DQN(
        q_func, optimizer, replay_buffer, gamma, explorer,
        replay_start_size=1000, minibatch_size=128, update_interval=1, target_update_interval=1000)

    # 手番と読み込むデータのパス取得
    if you == BLACK:
        file = os.path.join(BASE_DIR, 'static/ai/' + str(size) + '/agent_white_' + str(level*2))
        print(str(10000 + level))
        a = WHITE
    else:
        file = os.path.join(BASE_DIR, 'static/ai/' + str(size) + '/agent_black_' + str(level*2))
        a = BLACK
        board.change_turn()
    # AIの学習データ読み込み
    agent.load(file)
    # ---------------ここまでAiの設定-----------------

    # ---------------ここからオセロの処理-----------------
    # ゲームの処理、プレイヤー→AIの順に処理
    # プレイヤー処理
    board.pss = 0
    # 空だったらパス判定
    if place[0] == "" and place[1] == "":
        board.pss += 1

    board.change_turn()
    boardcopy = np.reshape(board.board.copy(), (-1,)) # ボードを1次元に変換
    pos = divmod(agent.act(boardcopy), size)
    # AI処理
    if not board.is_available(pos): # NNで置く場所が置けない場所であれば置ける場所からランダムに選択する．
        pos = board.random_action()
        if not len(board.available_pos) > 0: # 置く場所がなければパス
            board.pss += 1
        else:
            pos = divmod(pos, size) # 座標を2次元に変換
    if board.pss > 0 and not pos:
        print('パス')
    else:
        board.agent_action(pos) # posに石を置く
        board.pss = 0
    board.end_check() # ゲーム終了チェック
    board.available_reset()
    boardcopy = np.reshape(board.board.copy(), (-1,))
    # ---------------ここまでオセロの処理-----------------

    # ---------------ここからResponseの設定-----------------
    # 型が合わなくてjsonに変換できなかったので一度int型に変換
    boardArray = []
    for i in boardcopy:
        boardArray.append(int(i))

    # AIが置いた場所、パスであれば空で返却
    if pos:
        pos = (int(pos[1]), int(pos[0]))
    else:
        pos = ("", "")

    dict = OrderedDict([
        ('board', boardArray),
        ('agent_place', pos),
        ('status', getStatus(board, pos, a, you)),
        ('score', getScore(boardArray))
    ])

    # jsonに変換して返却
    ret = json.dumps(dict)
    print('----response----')
    print(ret)
    print()
    return JsonResponse(ret, safe=False)

# ステータスの取得、勝敗とパスの有無
def getStatus(board, pos, a, you):
    if board.game_end:
        return board.judge(a, you)
    if pos[0] == "" and pos[1] == "":
        return 'pass'
    return ''

# 今の石の数を取得
def getScore(board):
    b = 0
    w = 0
    for i in board:
        if i == 1:
            b = b + 1
        elif i == 2:
            w = w + 1
    return (b, w)
