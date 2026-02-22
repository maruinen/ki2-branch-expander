#!/usr/bin/python
# coding: shift_jis

import fileinput
import sys, codecs
import re
from copy import deepcopy

Gyoku = 1
Hisha = 2
Kaku  = 3
Kin   = 4
Gin   = 5
Kei   = 6
Kyo   = 7
Fu    = 8
Nari  = 16
Gote  = 32
possibleFrom = (  #駒毎のあり得る移動元の相対座標
    (),  #dummy
    #玉
    ( (0,1), (1,1), (1,0), (1,-1), (0,-1), (-1,-1), (-1,0), (-1,1)),
    #飛
    ( (0,-8), (0,-7), (0,-6), (0,-5), (0,-4), (0,-3), (0,-2), (0,-1), (0,1), (0,2), (0,3), (0,4), (0,5), (0,6), (0,7), (0,8),
      (-8,0), (-7,0), (-6,0), (-5,0), (-4,0), (-3,0), (-2,0), (-1,0), (1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0) ),
    #角
    ( (-8,-8), (-7,-7), (-6,-6), (-5,-5), (-4,-4), (-3,-3), (-2,-2), (-1,-1),
      (-8,8), (-7,7), (-6,6), (-5,5), (-4,4), (-3,3), (-2,2), (-1,1),
      (8,-8), (7,-7), (6,-6), (5,-5), (4,-4), (3,-3), (2,-2), (1,-1),
      (8,8), (7,7), (6,6), (5,5), (4,4), (3,3), (2,2), (1,1) ),
    #金
    ( (0,1), (-1,1), (1,1), (-1,0), (1,0), (0,-1) ),
    #銀
    ( (0,1), (-1,1), (1,1), (-1,-1), (1,-1) ),
    #桂
    ( (1,2), (-1,2) ),
    #香
    ( (0,1), (0,2), (0,3), (0,4), (0,5), (0,6), (0,7), (0,8) ),
    #歩
    ( (0,1), ),
    (),  #dummy
    (),  #dummy
    (),  #dummy
    (),  #dummy
    (),  #dummy
    (),  #dummy
    (),  #dummy
    (),  #dummy
    (),  #dummy
    #竜
    ( (0,-8), (0,-7), (0,-6), (0,-5), (0,-4), (0,-3), (0,-2), (0,-1), (0,1), (0,2), (0,3), (0,4), (0,5), (0,6), (0,7), (0,8),
      (-8,0), (-7,0), (-6,0), (-5,0), (-4,0), (-3,0), (-2,0), (-1,0), (1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0),
      (-1,-1), (-1,1), (1,-1), (1,1) ),
    #馬
    ( (-8,-8), (-7,-7), (-6,-6), (-5,-5), (-4,-4), (-3,-3), (-2,-2), (-1,-1),
      (-8,8), (-7,7), (-6,6), (-5,5), (-4,4), (-3,3), (-2,2), (-1,1),
      (8,-8), (7,-7), (6,-6), (5,-5), (4,-4), (3,-3), (2,-2), (1,-1),
      (8,8), (7,7), (6,6), (5,5), (4,4), (3,3), (2,2), (1,1),
      (0,1), (1,0), (0,-1), (-1,0) ),
    (),  #dummy
    #成銀
    ( (0,1), (-1,1), (1,1), (-1,0), (1,0), (0,-1) ),
    #成桂
    ( (0,1), (-1,1), (1,1), (-1,0), (1,0), (0,-1) ),
    #成香
    ( (0,1), (-1,1), (1,1), (-1,0), (1,0), (0,-1) ),
    #と
    ( (0,1), (-1,1), (1,1), (-1,0), (1,0), (0,-1) ),
    (),  #dummy
    (),  #dummy
    (),  #dummy
    (),  #dummy
    (),  #dummy
    (),  #dummy
    (),  #dummy
    )

class Board(object):
    def __init__(self):
        self.board = [
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [-1, Gote|Kyo, 0,          Gote|Fu, 0, 0, 0, Fu, 0,     Kyo, -1],
            [-1, Gote|Kei, Gote|Kaku,  Gote|Fu, 0, 0, 0, Fu, Hisha, Kei, -1],
            [-1, Gote|Gin, 0,          Gote|Fu, 0, 0, 0, Fu, 0,     Gin, -1],
            [-1, Gote|Kin, 0,          Gote|Fu, 0, 0, 0, Fu, 0,     Kin, -1],
            [-1, Gote|Gyoku, 0,        Gote|Fu, 0, 0, 0, Fu, 0,     Gyoku, -1],
            [-1, Gote|Kin, 0,          Gote|Fu, 0, 0, 0, Fu, 0,     Kin, -1],
            [-1, Gote|Gin, 0,          Gote|Fu, 0, 0, 0, Fu, 0,     Gin, -1],
            [-1, Gote|Kei, Gote|Hisha, Gote|Fu, 0, 0, 0, Fu, Kaku,  Kei, -1],
            [-1, Gote|Kyo, 0,          Gote|Fu, 0, 0, 0, Fu, 0,     Kyo, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]
            ]
        self.mochigomaS = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.mochigomaG = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.lastTo = 0

    def copy(self, src):
        self.board = deepcopy(src.board)
        self.mochigomaS = deepcopy(src.mochigomaS)
        self.mochigomaG = deepcopy(src.mochigomaG)
        self.lastTo = src.lastTo

    def printout(self):
        for y in range(1,10):
            for x in range(9,0,-1):
                komastr = u""
                if self.board[x][y] & Gote != 0:
                    komastr += u"v"
                else:
                    komastr += u" "
                komastr += u"　玉飛角金銀桂香歩　　　　　　　　王竜馬金全圭禾と"[self.board[x][y] & (Gote-1)]
                komastr += u" "
                print komastr,
            print
        print u"先手 %d %d %d %d %d %d %d %d %d" % tuple(self.mochigomaS)
        print u"後手 %d %d %d %d %d %d %d %d %d" % tuple(self.mochigomaG)
        
    def equals(self, b):
        return b.board == self.board and b.mochigomaS == self.mochigomaS and b.mochigomaG == self.mochigomaG
        
    def move1(self, move):
        gote = None
        koma = None
        (fromX, fromY) = (None, None)
        (toX, toY) = (None, None)
        place = False
        narigoma = False
        nari = False
        narazu = False
        uchi = False
        migi = False
        hidari = False
        sugu = False
        yuku = False
        hiku = False
        yoru = False
        cursor = 0
        errorStr = None

        #駒落ちコードの処理
        komaochiTable = {u"角落ち" : ((2,2),),
                       u"飛落ち" : ((8,2),),
                       u"飛車落ち" : ((8,2),),
                       u"二枚落ち" : ((2,2), (8,2)),
                       u"角香落ち" : ((2,2), (9,1)),
                       u"飛香落ち" : ((8,2), (1,1))}
        if move in komaochiTable:
            for (fromX, fromY) in komaochiTable[move]:
                self.board[fromX][fromY] = 0
            return
        
        while move != "":
            ch = move[0]
            move = move[1:]
            if ch == u'▲' or ch == u'▼':
                gote = False
            elif ch == u'▽' or ch == u'△':
                gote = True
            elif ch == u'王' or ch == u'玉':
                koma = Gyoku
            elif ch == u'飛':
                koma = Hisha
            elif ch == u'角':
                koma = Kaku
            elif ch == u'金':
                koma = Kin
            elif ch == u'銀':
                koma = Gin
            elif ch == u'桂':
                koma = Kei
            elif ch == u'香':
                koma = Kyo
            elif ch == u'歩':
                koma = Fu
            elif ch == u'龍'or ch == u'竜':
                koma = Hisha
                narigoma = True
            elif ch == u'馬':
                koma = Kaku;
                narigoma = True
            elif ch == u'と':
                koma = Fu;
                narigoma = True
            elif ch == u'成':
                if koma is None:
                    narigoma = True
                elif not narazu:
                    nari = True
            elif ch == u'不':
                narazu = True
            elif ch == u'同':
                toX = self.lastTo / 10;
                toY = self.lastTo % 10;
            elif ch == u'打':
                uchi = True
            elif ch == u'右':
                migi = True
            elif ch == u'左':
                hidari = True
            elif ch == u'上' or ch == u'行':
                yuku = True
            elif ch == u'引':
                hiku = True
            elif ch == u'直':
                sugu = True
            elif ch == u'寄':
                yoru = True
            elif ch == u' ' or ch == u'　':
                pass
            else:
                try:
                    digit = u"０１２３４５６７８９零一二三四五六七八九".index(ch)
                    digit = digit % 10
                    if (toX is None):
                        toX = digit
                    else:
                        toY = digit
                except ValueError:
                    raise ValueError, "unknown char:" + ch

        if gote is None or koma is None:
            return
        
        if gote:
            factor = -1
        else:
            factor = 1

        if narigoma:
            nkoma = koma | Nari
        else:
            nkoma = koma  #成駒を含めた駒種別

        if gote:
            ngkoma = nkoma | Gote
        else:
            ngkoma = nkoma  #手番を含めた駒種別

        (likelyFromX, likelyFromY) = (None, None)  #possibleFrom[nkoma]上の最新のそれらしい候補
        if not uchi:
            for possibleX,possibleY in possibleFrom[nkoma]:
                x = toX + factor * possibleX
                y = toY + factor * possibleY
                if 1 <= x and x <= 9 and 1 <= y and y <= 9 and (
                    #移動元がその駒か
                    self.board[x][y] == ngkoma or
                    #移動元が成る前の駒で、これから成る
                    nari and self.board[x][y] == ngkoma and
                    #行き先が敵陣か移動元が敵陣
                    #（そこに行ける駒が複数あっても、成れる駒が1つに特定
                    #できる場合（敵陣外への成り）があるので、絞る）
                    (gote and (toY >= 7 or y >= 7) or not gote and (toY <= 3 or y <= 3))
                    ):
                    #飛び駒の途中障害物なし検査
                    if koma == Hisha or koma == Kaku or nkoma == Kyo:
                        dx = 0
                        dy = 0
                        if possibleX > 0: dx = 1
                        if possibleX < 0: dx = -1
                        if possibleY > 0: dy = 1
                        if possibleY < 0: dy = -1
                        tx = toX + factor * dx
                        ty = toY + factor * dy
                        while tx != x or ty != y:
                            if self.board[tx][ty] > 0: break
                            tx += factor * dx
                            ty += factor * dy
                        if tx != x or ty != y: continue #for i loop
                    if likelyFromX is None:
                        #1つ目の候補ならそのまま記録
                        (likelyFromX, likelyFromY) = (possibleX, possibleY)
                    else:
                        # 右、左、上／行、引、直、寄の解決
                        if migi:
                            if possibleX < likelyFromX:
                                #「右」で最も右なら直ちに採用する
                                (likelyFromX, likelyFromY) = (possibleX, possibleY)
                            elif possibleX == likelyFromX:
                                if yuku or hiku or yoru:
                                    #エラーとしない
                                    if yuku and possibleY > likelyFromY or hiku and possibleY < likelyFromY or yoru and possibleY == 0:
                                        (likelyFromX, likelyFromY) = (possibleX, possibleY)
                                else:
                                    errorStr = u"「右」で解決できません"
                        elif hidari:
                            if possibleX > likelyFromX:
                                #「左」で最も左なら直ちに採用する
                                (likelyFromX, likelyFromY) = (possibleX, possibleY)
                            elif possibleX == likelyFromX:
                                if yuku or hiku or yoru:
                                    #エラーとしない
                                    if yuku and possibleY > likelyFromY or hiku and possibleY < likelyFromY or yoru and possibleY == 0:
                                        (likelyFromX, likelyFromY) = (possibleX, possibleY)
                                else:
                                    errorStr = u"「左」で解決できません"
                        elif yuku:
                            if possibleY == likelyFromY and possibleY > 0:  #上がらない候補は重複しても無視する
                                errorStr = u"「上／行」で解決できません"
                            elif possibleY > likelyFromY:
                                (likelyFromX, likelyFromY) = (possibleX, possibleY)
                        elif hiku:
                            if possibleY == likelyFromY and possibleY < 0:  #下がらない候補は重複しても無視する
                                errorStr = u"「引」で解決できません"
                            elif possibleY < likelyFromY:
                                (likelyFromX, likelyFromY) = (possibleX, possibleY)
                        elif sugu:
                            if possibleX == likelyFromX and possibleY > 0 and likelyFromY > 0:
                                errorStr = u"「直」で解決できません"
                            elif possibleX == 0 and possibleY > 0:
                                (likelyFromX, likelyFromY) = (possibleX, possibleY)
                        elif yoru:
                            if possibleY == likelyFromY and possibleY == 0:  #寄らない候補は重複しても無視する
                                errorStr = u"「寄」で解決できません"
                            elif possibleY == 0:
                                (likelyFromX, likelyFromY) = (possibleX, possibleY)
                        else:
                            errorStr = u"2つ以上の候補があります"

        if likelyFromX is not None:  #移動元が見つかった
            fromX = toX + factor * likelyFromX
            fromY = toY + factor * likelyFromY
        else:
            #打にできそうなら打にする
            if (gote and self.mochigomaG[koma] > 0 or not gote and self.mochigomaS[koma] > 0) \
                    and not narigoma and not nari \
                    and not migi and not hidari and not yuku and not hiku and not sugu and not yoru:
                uchi = True
            else:
                errorStr = "koma=%d, nkoma=%d" % (koma, nkoma)

        # 駒の移動
        if uchi:
            if self.board[toX][toY] != 0:  #打ちながらは取れない
                errorStr = u"打ちながらは取れない"
            else:
                self.board[toX][toY] = koma
                if gote:
                    self.board[toX][toY] = self.board[toX][toY] | Gote
                    self.mochigomaG[koma] = self.mochigomaG[koma] - 1
                else:
                    self.mochigomaS[koma] = self.mochigomaS[koma] - 1
        elif fromX > 0 and fromY > 0:
            if self.board[toX][toY] != 0:  #取り
                if gote:
                    self.mochigomaG[self.board[toX][toY] & (Nari-1)] = self.mochigomaG[self.board[toX][toY] & (Nari-1)] + 1
                else:
                    self.mochigomaS[self.board[toX][toY] & (Nari-1)] = self.mochigomaS[self.board[toX][toY] & (Nari-1)] + 1
            self.board[toX][toY] = self.board[fromX][fromY]
            if nari:
                self.board[toX][toY] |= Nari
            if gote:
                self.board[toX][toY] |= Gote
            self.board[fromX][fromY] = 0
        else:
            errorStr = "some error"

        self.lastTo = toX * 10 + toY  #「同」のために記録する
        if errorStr is not None:
            print "error:", move, errorStr
            return 1

        #moves = moves + 1
        #this.draw();
        return 0

#sys.stdin  = codecs.getreader('shift_jis')(sys.stdin)
#sys.stdin = codecs.getwriter('utf-8')(sys.stdin)
sys.stdout = codecs.getwriter('utf-8')(sys.stdout)
#sys.stdout  = codecs.getwriter('euc_jp')(sys.stdout)

kifs = []

for filename in sys.argv[1:]:
#   file = codecs.open(filename, 'r', 'shift-jis')
    file = codecs.open(filename, 'r', 'cp932')
#   file = codecs.open(filename, 'r', 'utf-8')

    kif = ""
    for line in file.readlines():
        if line == "\n":
            kifs.append(kif)
            kif = ""
        else:
            kif += line

    file.close()

    if kif != "":
        kifs.append(kif)

#for kif in kifs:
#    print kif.replace("\n", " ")



board = Board()
board.printout()

boardDict = dict()
labelDict = dict()
mergeDict = dict()

#b1 = deepcopy(board)
for k in range(0, len(kifs)):
    kif = kifs[k]
    b1 = Board()
    kif1 = kif.split("\n")
    branch = False
    for m in range(0, len(kif1)):
        move = kif1[m].rstrip()
        print "Move %d:" % m, move

        for (kk,kv) in boardDict.iteritems():
            (k_, m_) = kk
            if k != k_ and kv.equals(b1):
                if branch:
                    print "before this move:(kif=%d,move=%d) is equal to (kif=%d,move=%d)!" % (k, m, k_, m_)

        b1.move1(move)
        hit = False
        for (kk,kv) in boardDict.iteritems():
            (k_, m_) = kk
            if k != k_ and kv.equals(b1):
                hit = True
                if branch:
                    print "(kif=%d,move=%d) is equal to (kif=%d,move=%d)!" % (k, m, k_, m_)
                    if (k_,m_) not in labelDict:
                        labelDict[k_,m_] = len(labelDict) + 1
                    mergeDict[k,m] = labelDict[k_,m_]
                    branch = False
                else:
                    #分岐でなければ一致してもマージしない
                    #但し、符号が違えば、次からマージ対象とする為に分岐する
                    kif2 = kifs[k_].split("\n")
                    move1 = kif1[m].rstrip()
                    move2 = kif2[m_].rstrip()
                    if move1 == move2:
                        print "(not a branch)"
                    else:
                        print "not a branch but move string differ(", move1, "and", move2, ") => branching from next";
                        branch = True
        if not hit:
            boardDict[k,m] = deepcopy(b1)
            branch = True
#        b1.printout()
#    b1.printout()
print "--- output start ---"

dat = codecs.open("Kifs_sorted.txt", "w", "shift-jis")

for k in range(0, len(kifs)):
    kif = kifs[k]
    kif1 = kif.split("\n")
    for m in range(0, len(kif1)):
        move = kif1[m].rstrip()
        if (k,m) in labelDict:
            move += "\t#label %03d" % labelDict[k,m]
        if move != "" and (k,m) in mergeDict:
            move += "\t#merge %03d" % mergeDict[k,m]
        dat.write(move + "\n")
dat.close()
