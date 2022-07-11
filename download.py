import pandas as pd
import sqlite3
import os

DB_FOLDER = "data"
DB_NAME = "jleague.db"

"""
Jリーグ公式サイトからのデータ収集
"""
def download_result(year, competition=0):
    """
    Jリーグの公式記録ページから、勝敗記録を取得する。
    
    API等は無いのでHTMLから取得するが、必要データはtableタグのみであり、pandasで取得
    戻り値はDataFrame型
    """
    if competition == 0:
        url = 'https://data.j-league.or.jp/SFMS01/search?competition_years='+ str(year)
    else:
        url = 'https://data.j-league.or.jp/SFMS01/search?competition_years='+ str(year) + '&competition_frame_ids=' + str(competition)
    dfs = pd.io.html.read_html(url)
    # 取得したDataFrameの一番目が結果表
    #df = dfs[0].drop(['インターネット中継・TV放送','入場者数'],axis=1) # 結果に関係なさそうな放送局と入場者数はこの時点で削除しておく
    return dfs[0]
    
def download_all_results(db_file=DB_NAME, db_folder=DB_FOLDER, start=1992, end=2022):
    """
    Jリーグの公式記録ページから、勝敗記録を取得し、SQLite3データベース化する。
    start年～end年のデータを取得
    """
    result = pd.DataFrame()
    for year in range(start,end):
        df = download_result(year)
        result = pd.concat([result, df])
    
    db_name = db_folder + '/' + db_file
    if os.path.exists(db_folder) == False:
        os.mkdir(db_folder)
    conn = sqlite3.connect(db_name) # DB接続
    result.to_sql("result", conn, if_exists="replace") # DFをDBに変換
    conn.close()
    
def get_db_data(data="result",db_file=DB_NAME, db_folder=DB_FOLDER):
    """
    保存済みのデータをpandas data frameとして取得
    """
    db_name = db_folder + '/' + db_file
    conn = sqlite3.connect(db_name)
    df = pd.read_sql("select * from " + data, conn)
    conn.close()
    return df
    
"""
Football-Labからのデータ収集
"""
def _rename_team_by_record(rank):
    record = get_db_data()
    teams = pd.concat([record["ホーム"],record["アウェイ"]]).drop_duplicates()
    for i in range(len(rank["チーム"])):
        for team in teams:
            if rank.loc[i, "チーム"].endswith(team) is True:
                rank.loc[i, "チーム"] = team
    return rank
    
def fl_get_rank(competition=1, year=2018):
    """
    順位表の取得
    """
    url = "http://www.football-lab.jp/summary/team_ranking/j" + str(competition) + "/?year=" + str(year)
    dfs = pd.io.html.read_html(url)
    rank = dfs[0].drop("Unnamed: 1",axis=1).rename(columns={"Unnamed: 2":"チーム"})
    rank = _rename_team_by_record(rank)
    return rank

def fl_get_chance_rate(competition=1, year=2018):
    """
    チャンス構築率の取得
    """
    url = "http://www.football-lab.jp/summary/team_ranking/j" + str(competition) + "/?year=" + str(year) + "&data=chance"
    dfs = pd.io.html.read_html(url)
    attack = dfs[0].drop("Unnamed: 0",axis=1)
    attack = attack.drop("Unnamed: 3",axis=1)
    attack = attack.drop("Unnamed: 5",axis=1)
    attack = attack.drop("Unnamed: 7",axis=1)
    attack = attack.drop("Unnamed: 9",axis=1)
    attack = attack.drop("Unnamed: 11",axis=1)
    attack = attack.rename(columns={"Unnamed: 1":"チーム"})
    attack = _rename_team_by_record(attack)
    defense = dfs[2].drop("Unnamed: 0",axis=1)
    defense = defense.drop("Unnamed: 3",axis=1)
    defense = defense.drop("Unnamed: 5",axis=1)
    defense = defense.drop("Unnamed: 7",axis=1)
    defense = defense.drop("Unnamed: 9",axis=1)
    defense = defense.drop("Unnamed: 11",axis=1)
    defense = defense.rename(columns={"Unnamed: 1":"チーム"})
    defense = _rename_team_by_record(defense)
    return attack, defense

import requests
import re
import ast
from bs4 import BeautifulSoup,Comment
def fl_get_goal_pattern(competition=1, year=2018):
    """
    ゴールパターンの取得
    """
    url = "http://www.football-lab.jp/summary/team_ranking/j" + str(competition) + "/?year=" + str(year) + "&data=goal"
    response = requests.get(url)
    bs = BeautifulSoup(response.content,"lxml")
    test=str(bs.find(string=re.compile("function drawChart")))
    tbl = re.search(r'arrayToDataTable\((.*?)\)', test, flags=re.DOTALL|re.MULTILINE).group(1)
    return pd.DataFrame(ast.literal_eval(tbl)[1:],columns=ast.literal_eval(tbl)[0])

def fl_get_lost_pattern(competition=1, year=2018):
    """
    失点パターンの取得
    """
    url = "http://www.football-lab.jp/summary/team_ranking/j" + str(competition) + "/?year=" + str(year) + "&data=lost"
    response = requests.get(url)
    bs = BeautifulSoup(response.content,"lxml")
    test=str(bs.find(string=re.compile("function drawChart")))
    tbl = re.search(r'arrayToDataTable\((.*?)\)', test, flags=re.DOTALL|re.MULTILINE).group(1)
    return pd.DataFrame(ast.literal_eval(tbl)[1:],columns=ast.literal_eval(tbl)[0])

def fl_get_possession(competition=1, year=2018):
    """
    ボール支配率の取得
    """
    url = "http://www.football-lab.jp/summary/team_ranking/j" + str(competition) + "/?year=" + str(year) + "&data=possession"
    response = requests.get(url)
    bs = BeautifulSoup(response.content,"lxml")
    test=str(bs.find(string=re.compile("function drawChart"))).replace("(%)","%")    # なぜか(%)のところが変換できないので文字列として変換
    tbl = re.search(r'arrayToDataTable\((.*?)\)', test, flags=re.DOTALL|re.MULTILINE).group(1)
    tbl = re.sub(", \{.+?\}","", tbl)   # annotation属性が残ってしまうので削除
    col = ast.literal_eval(tbl)[0]
    col.append("dummy")
    return pd.DataFrame(ast.literal_eval(tbl)[1:],columns=col).drop("dummy",axis=1) # 不必要な列があるのでdummyと命名して削除

def fl_get_cbp(competition=1, year=2018, data=None):
    """
    チャンスビルディングポイントの取得
    """
    url = "http://www.football-lab.jp/summary/cbp_ranking/j" + str(competition) + "/?year=" + str(year)
    if data != None:
        url += "&data=" + data
    dfs = pd.io.html.read_html(url)
    cbp = dfs[0].drop("Unnamed: 0",axis=1).drop("Unnamed: 1",axis=1).rename(columns={"Unnamed: 2":"チーム"})
    cbp = _rename_team_by_record(cbp)
    cbp = cbp.drop("順位",axis=1).drop("勝点",axis=1).drop("得点",axis=1).drop("失点",axis=1).drop("試合平均",axis=1)
    if "最近５試合" in list(cbp.keys()):
        cbp = cbp.drop("最近５試合",axis=1)
    return cbp

def fl_get_all_data(competition=1, year=2018):
    rank = fl_get_rank(competition,year)
    atk, dfe = fl_get_chance_rate(competition=competition,year=year)
    goal_pat = fl_get_goal_pattern(competition=competition, year=year)
    goal_pat = goal_pat.rename(columns={"ＰＫ":"ＰＫ_得点",
                                        "セットプレー直接":"セットプレー直接_得点",
                                        "セットプレーから":"セットプレーから_得点",
                                        "クロスから":"クロスから_得点",
                                        "スルーパスから":"スルーパスから_得点",
                                        "ショートパスから":"ショートパスから_得点",
                                        "ロングパスから":"ロングパスから_得点",
                                        "ドリブルから":"ドリブルから_得点",
                                        "こぼれ球から":"こぼれ球から_得点",
                                        "その他":"その他_得点"
                                       })
    lost_pat = fl_get_lost_pattern(competition=competition, year=year)
    lost_pat = lost_pat.rename(columns={"ＰＫ":"ＰＫ_失点",
                                        "セットプレー直接":"セットプレー直接_失点",
                                        "セットプレーから":"セットプレーから_失点",
                                        "クロスから":"クロスから_失点",
                                        "スルーパスから":"スルーパスから_失点",
                                        "ショートパスから":"ショートパスから_失点",
                                        "ロングパスから":"ロングパスから_失点",
                                        "ドリブルから":"ドリブルから_失点",
                                        "こぼれ球から":"こぼれ球から_失点",
                                        "その他":"その他_失点"
                                       })
    posession = fl_get_possession(competition=competition,year=year)
    CBP_DATA = [None,"pass","dribble","cross","cross","shot","defense","save"]
    cbp = []
    for cbp_data in CBP_DATA:
        cbp.append(fl_get_cbp(competition=competition, year=year, data=cbp_data))

    fl_data = pd.merge(rank, atk, on="チーム")
    fl_data = pd.merge(fl_data, dfe, on="チーム")
    fl_data = pd.merge(fl_data, goal_pat, on="チーム")
    fl_data = pd.merge(fl_data, lost_pat, on="チーム")
    fl_data = pd.merge(fl_data, posession, on="チーム")
    for i in range(len(CBP_DATA)):
        fl_data = pd.merge(fl_data, cbp[i], on="チーム")
    fl_data["年度"] = year
    fl_data["ディビジョン"] = "J" + str(competition)
    return fl_data

from datetime import datetime
def download_all_fl_data(db_file=DB_NAME, db_folder=DB_FOLDER):
    """
    2012年から実行した年までのFootball-Labのデータを収集し
    DB(Sqlite3)へ保存
    """
    data = pd.DataFrame()
    latest_year = int(datetime.now().strftime("%Y"))
    for year in range(2012,latest_year+1):
        for division in range(1,3):
            data = pd.concat([data,fl_get_all_data(competition=division, year=year)])
    # データをDBへ保存
    db_name = db_folder + '/' + db_file
    if os.path.exists(db_folder) == False:
        os.mkdir(db_folder)
    conn = sqlite3.connect(db_name) # DB接続
    data.to_sql("data", conn, if_exists="replace") # DFをDBに変換
    conn.close()
    return data

"""
TOTO公式サイトからの予定データ収集
"""
def _process_toto_frame(tmp):
    """
    TOTOの予定データを見やすい形に編集
    """
    return tmp[1:].drop(0,axis=1).drop(5,axis=1).rename(columns={1:tmp[1][0],2:tmp[2][0],3:tmp[3][0],4:"ホーム",6:"アウェイ"})

TOTO_DB = "data/toto.db"
def _get_toto_db():
    """
    TOTOの予定データのチーム名・スタジアム名を公式記録上のデータに変換するDBデータを取得
    (直近100回分の開催データを収集してDB作成)
    """
    conn = sqlite3.connect(TOTO_DB)
    team_df = pd.io.sql.read_sql_query("SELECT * from team", conn)
    studium_df = pd.io.sql.read_sql_query("SELECT * from studium", conn)
    conn.close()
    team_df = team_df.set_index("TOTO",drop=True)
    studium_df = studium_df.set_index("TOTO",drop=True)
    return team_df, studium_df
    
def _change_names(tmp, team_df, studium_df):
    """
    TOTOの予定データのチーム名・スタジアム名を公式記録上のデータに変換
    """
    for i in range(len(tmp)):
        tmp.iloc[i]["ホーム"] = team_df["公式記録"][tmp.iloc[i]["ホーム"]]
        tmp.iloc[i]["アウェイ"] = team_df["公式記録"][tmp.iloc[i]["アウェイ"]]
        for j in range(len(studium_df)):
            if tmp.iloc[i]["競技場"] == studium_df.index[j]:
                tmp.iloc[i]["競技場"] = studium_df.iloc[j]["公式記録"]
                break
    return tmp

def get_toto_schedule(holdCntId):
    """
    TOTOの対象ゲームを収集
    <引数>holdCntId: 開催回
    直近100回分の開催データから、公式記録の名称との変換DBを作成したので、これをもとにチーム名・スタジアム名を変換する
    """
    toto = None
    miniA = None
    miniB = None
    goal = None
    url = "http://sport-kuji.toto-dream.com/dci/I/IPA/IPA01.do?op=disptotoLotInfo&holdCntId=%04d" % holdCntId
    dfs = pd.io.html.read_html(url)
    team_df, studium_df = _get_toto_db()
    for df in dfs:
        if len(df)>=2 and df[1][0]=="開催日":
            if len(df)==14:
                toto = _process_toto_frame(df)
                toto = _change_names(toto, team_df, studium_df)
            elif len(df) == 6:
                if miniA is None:
                    miniA = _process_toto_frame(df)
                    miniA = _change_names(miniA, team_df, studium_df)
                else:
                    miniB = _process_toto_frame(df)
                    miniB = _change_names(miniB, team_df, studium_df)
            elif len(df) == 4 or len(df) == 3:
                goal = _process_toto_frame(df)
                goal = _change_names(goal, team_df, studium_df)
    return toto, miniA, miniB, goal
