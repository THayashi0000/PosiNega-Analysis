# モジュールのインポート
import re
import csv
import time
import pandas as pd
import matplotlib.pyplot as plt
import MeCab
import random
from statistics import mean

# CSVファイルの読み込み(CSVファイルは"id"と”text”の列が必須)
input_file='input.csv'
tw_df = pd.read_csv(input_file, encoding='utf-8')

# PN Tableの読み込み
pn_df = pd.read_csv('pn_ja.dic.txt',\
                    sep=':',
                    encoding='shift-jis',
                    names=('Word','Reading','POS', 'PN')
                   )

# PN Tableをデータフレームから辞書型に変換
word_list = list(pn_df['Word'])
pn_list = list(pn_df['PN'])  # 中身の型はnumpy.float64
pn_dict = dict(zip(word_list, pn_list))

# 本文テキストから改行を排除
text_list = list(tw_df['text'])
for i in range(len(text_list)):
    text_list[i] = text_list[i].replace('\n', ' ')

# MeCabインスタンス作成
m = MeCab.Tagger('')  # 指定しなければIPA辞書
# -----テキストを形態素解析して辞書のリストを返す関数----- #
def get_diclist(text):
    parsed = m.parse(text)      # 形態素解析結果（改行を含む文字列として得られる）
    lines = parsed.split('\n')  # 解析結果を1行（1語）ごとに分けてリストにする
    lines = lines[0:-2]         # 後ろ2行は不要なので削除
    diclist = []
    for word in lines:
        l = re.split('\t|,',word)  # 各行はタブとカンマで区切られてるので
        d = {'Surface':l[0], 'POS1':l[1], 'POS2':l[2], 'BaseForm':l[7]}
        diclist.append(d)
    return(diclist)


# 形態素解析結果の単語ごと辞書型データにPN値を追加する関数
def add_pnvalue(diclist_old):
    diclist_new = []
    for word in diclist_old:
        base = word['BaseForm']        # 個々の辞書から基本形を取得
        if base in pn_dict:
            pn = float(pn_dict[base])  # 中身の型があれなので
        else:
            pn = 'notfound'            # その語がPN Tableになかった場合
        word['PN'] = pn
        diclist_new.append(word)
    return(diclist_new)

# 各投稿のPN平均値をとる関数
def get_pnmean(diclist):
    pn_list = []
    for word in diclist:
        pn = word['PN']
        if pn != 'notfound':
            pn_list.append(pn)  # notfoundだった場合は追加もしない
    if len(pn_list) > 0:        # 「全部notfound」じゃなければ
        pnmean = mean(pn_list)
    else:
        pnmean = 0              # 全部notfoundならゼロにする
    return(pnmean)

# pn値のリストを作成（一応時間を測りました）
start_time = time.time()               ### ▼時間計測▼ ###
pnmeans_list = []
for tw in tw_df['text']:
    dl_old = get_diclist(tw)
    dl_new = add_pnvalue(dl_old)
    pnmean = get_pnmean(dl_new)
    pnmeans_list.append(pnmean)
print('処理時間は' + str(time.time() - start_time) + '秒です')        ### ▲時間計測▲ ###

# ID、本文、PN値を格納したデータフレームを作成
aura_df = pd.DataFrame({'id':tw_df['id'],
                        'text':text_list,
                        'PN':pnmeans_list,
                       },
                       columns=['id', 'text', 'PN']
                      )

# PN値の昇順でソート
aura_df = aura_df.sort_values(by='PN', ascending=True)

# CSVを出力（ExcelでみたいならUTF8ではなくShift-JISを指定）
aura_df.to_csv(input_file[:-3] +'PosiNega.csv',\
                index=None,\
                encoding='utf-8',\
                quoting=csv.QUOTE_NONNUMERIC\
               )
