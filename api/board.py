import numpy as np
import sys
import re # 正規表現
import random
import copy
# 定数定義 #
NONE = 0   # ボードのある座標にある石：なし
BLACK = 1  # ボードのある座標にある石：黒
WHITE = 2  # ボードのある座標にある石：白
AVAILABLE = 3 # ボードのある座標にある置ける場所
STONE = [' ', '●', '○'] # 石の表示用
ROWLABEL = {'a':1, 'b':2, 'c':3, 'd':4, 'e':5, 'f':6, 'g':7, 'h':8} # ボードの横軸ラベル
N2L = ['', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'] # 横軸ラベルの逆引き用
REWARD_WIN = 1 # 勝ったときの報酬
REWARD_LOSE = -1 # 負けたときの報酬
# 2次元のボード上での隣接8方向の定義（左から，上，右上，右，右下，下，左下，左，左上）
DIR = ((-1,0), (-1,1), (0,1), (1,1), (1,0), (1, -1), (0,-1), (-1,-1))

#### リバーシボードクラス ###
class Board():

    # インスタンス
    def __init__(self, size):
        self.board_reset(size)

    # ボードの初期化
    def board_reset(self, size):
        self.size = size
        self.board = np.zeros((self.size, self.size), dtype=np.float32) # 全ての石をクリア．ボードは2次元配列（i, j）で定義する．
        mid = self.size // 2 # 真ん中の基準ポジション
        # 初期4つの石を配置
        self.board[mid, mid] = WHITE
        self.board[mid-1, mid-1] = WHITE
        self.board[mid-1, mid] = BLACK
        self.board[mid, mid-1] = BLACK
        self.winner = NONE # 勝者
        self.turn = BLACK  # 黒石スタート
        self.game_end = False # ゲーム終了チェックフラグ
        self.pss = 0 # パスチェック用フラグ．双方がパスをするとゲーム終了
        self.nofb = 0 # ボード上の黒石の数
        self.nofw = 0 # ボード上の白石の数
        self.available_pos = self.search_positions() # self.turnの石が置ける場所のリスト

    # 石を置く&リバース処理
    def put_stone(self, pos):
        if self.is_available(pos):
            self.board[pos[0], pos[1]] = self.turn
            self.do_reverse(pos) # 石のリバース
            return True
        else:
            return False

    # 白黒のターンチェンジ
    def change_turn(self):
        self.turn = WHITE if self.turn == BLACK else BLACK
        self.available_pos = self.search_positions() # 石が置ける場所を探索しておく

    # ランダムに石を置く場所を決める（ε-greedy用）
    def random_action(self):
        self.available_pos = self.search_positions()
        if len(self.available_pos) > 0:
            if len(self.available_pos) == 1:
                pos = self.available_pos[0]
                pos = pos[0] * self.size + pos[1] # 1次元座標に変換（NNの教師データは1次元でないといけない）
                return pos
            pos = random.choice(self.available_pos) # 置く場所をランダムに決める
            pos = pos[0] * self.size + pos[1] # 1次元座標に変換（NNの教師データは1次元でないといけない）
            return pos
        return False # 置く場所なし

    # エージェントのアクションと勝敗判定
    def agent_action(self, pos):
        self.put_stone(pos)
        self.end_check()

    # リバース処理
    def do_reverse(self, pos):
        for di, dj in DIR:
            opp = BLACK if self.turn == WHITE else WHITE # 対戦相手の石
            boardcopy = self.board.copy() # 一旦ボードをコピーする（copyを使わないと参照渡しになるので注意）
            i = pos[0]
            j = pos[1]
            flag = False # 挟み判定用フラグ
            while 0 <= i < self.size and 0 <= j < self.size: # (i,j)座標が盤面内に収まっている間繰り返す
                i += di # i座標（縦）をずらす
                j += dj # j座標（横）をずらす
                if 0 <= i < self.size and 0 <= j < self.size and boardcopy[i,j] == opp:  # 盤面に収まっており，かつ相手の石だったら
                    flag = True
                    boardcopy[i,j] = self.turn # 自分の石にひっくり返す
                elif not(0 <= i < self.size and 0 <= j < self.size) or (flag == False and boardcopy[i,j] != opp):
                    break
                elif boardcopy[i,j] == self.turn and flag == True: # 自分と同じ色の石がくれば挟んでいるのでリバース処理を確定
                    self.board = boardcopy.copy() # ボードを更新
                    break

    # 石が置ける場所をリストアップする．石が置ける場所がなければ「パス」となる
    def search_positions(self):
        self.available_reset()
        pos = []
        emp = np.where(self.board == 0) # 石が置かれていない場所を取得
        for i in range(emp[0].size): # 石が置かれていない全ての座標に対して
            p = (emp[0][i], emp[1][i]) # (i,j)座標に変換
            if self.is_available(p):
                pos.append(p) # 石が置ける場所の座標リストの生成

                if self.size == 6: # 6x6のみ置ける場所も渡して学習してみたので
                    self.board[p[0], p[1]] = AVAILABLE # 石が置ける場所をボードにセット
        return pos

    # 置ける場所のリセットを行う
    def available_reset(self):
        pos = []
        emp = np.where(self.board == 3) # 石が置ける場所を取得
        for i in range(emp[0].size):
            self.board[emp[0][i], emp[1][i]] = NONE # 石がない場所としてリセット

    # 石が置けるかをチェックする
    def is_available(self, pos):
        if self.board[pos[0], pos[1]] == BLACK or self.board[pos[0], pos[1]] == WHITE: # 黒 or 白 が置いてあると置けない
            return False
        opp = BLACK if self.turn == WHITE else WHITE
        for di, dj in DIR: # 8方向の挟み（リバースできるか）チェック
            i = pos[0]
            j = pos[1]
            #import pdb; pdb.set_trace()
            flag = False # 挟み判定用フラグ
            while 0 <= i < self.size and 0 <= j < self.size: # (i,j)座標が盤面内に収まっている間繰り返す
                i += di # i座標（縦）をずらす
                j += dj # j座標（横）をずらす
                if 0 <= i < self.size and 0 <= j < self.size and self.board[i,j] == opp: #盤面に収まっており，かつ相手の石だったら
                    flag = True
                elif not(0 <= i < self.size and 0 <= j < self.size) or (flag == False and self.board[i,j] != opp) or self.board[i,j] == NONE:
                    break
                elif self.board[i,j] == self.turn and flag == True: # 自分と同じ色の石
                    return True
        return False

    # ゲーム終了チェック
    def end_check(self):
        self.available_reset()
        if np.count_nonzero(self.board) == self.size * self.size or self.pss == 2: # ボードに全て石が埋まるか，双方がパスがしたら
            self.game_end = True
            self.nofb = len(np.where(self.board==BLACK)[0])
            self.nofw = len(np.where(self.board==WHITE)[0])
            if len(np.where(self.board==BLACK)[0]) > len(np.where(self.board==WHITE)[0]):
                self.winner = BLACK
            elif len(np.where(self.board==BLACK)[0]) < len(np.where(self.board==WHITE)[0]):
                self.winner = WHITE
            elif len(np.where(self.board==BLACK)[0]) == len(np.where(self.board==WHITE)[0]):
                self.winner = NONE

    def judge(self, a, you):
        if self.winner == a:
            return 'lose'
        elif self.winner == you:
            return 'win'
        else:
            return 'draw'
