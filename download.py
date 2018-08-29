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
    df = dfs[0].drop(['インターネット中継・TV放送','入場者数'],axis=1) # 結果に関係なさそうな放送局と入場者数はこの時点で削除しておく
    return dfs[0]
    
def download_all_results(db_file=DB_NAME, db_folder=DB_FOLDER):
    """
    Jリーグの公式記録ページから、勝敗記録を取得し、SQLite3データベース化する。
    1992年～2017年のデータを取得
    """
    result = pd.DataFrame()
    for year in range(1992,2018):
        df = download_result(year)
        result = pd.concat([result, df])
    
    db_name = db_folder + '/' + db_file
    if os.path.exists(db_folder) == False:
        os.mkdir(db_folder)
    conn = sqlite3.connect(db_name) # DB接続
    result.to_sql("result", conn, if_exists="replace") # DFをDBに変換
    
def get_db_data(db_file=DB_NAME, db_folder=DB_FOLDER):
    """
    保存済みのデータをpandas data frameとして取得
    """
    db_name = db_folder + '/' + db_file
    conn = sqlite3.connect(db_name)
    df = pd.read_sql("select * from result", conn)
    conn.close()
    return df
    
def processing_data(df):
    """
    不要なデータ、同じ意味だが違う表記のデータを書き換える
    """
    df = _processing_noneed_data(df)
    df = _processing_rename_team(df)
    df = _processing_rename_studium(df)
    return df

def processing_db_update(db_file=DB_NAME, db_folder=DB_FOLDER):
    """
    指定したDBファイルのデータについて、processing_dataで定義される加工を行い更新する
    """
    db_name = db_folder + '/' + db_file
    if os.path.exists(db_name) is True:
        conn = sqlite3.connect(db_name)
        df = pd.read_sql("select * from result", conn)
        conn.close()
        df = processing_data(df)
        os.remove(db_name)
        conn = sqlite3.connect(db_name)
        df.to_sql("result", conn, if_exists="replace")
        conn.close()
    else:
        print("No dbfile:" + db_name)
    
def _processing_noneed_data(df):
    """
    不要データを削除
    """
    df = df.drop("index",axis=1)
    df = df.drop("インターネット中継・TV放送",axis=1)
    df = df.drop("入場者数",axis=1)
    df = df[df["大会"]!="サテライトリーグ"].reset_index(drop=True)
    df = df[df["大会"]!="サテライトリーグ Ａグループ"].reset_index(drop=True)
    df = df[df["大会"]!="サテライトリーグ Ｂグループ"].reset_index(drop=True)
    df = df[df["大会"]!="サテライトリーグ Ｃグループ"].reset_index(drop=True)
    df = df[df["大会"]!="サテライトリーグ Ｄグループ"].reset_index(drop=True)
    df = df[df["大会"]!="サテライトリーグ Ｅグループ"].reset_index(drop=True)
    df = df[df["大会"]!="サテライトリーグ Ｆグループ"].reset_index(drop=True)
    df = df[df["大会"]!="オールスター"].reset_index(drop=True)
    df = df[df["大会"]!="ドリームマッチ"].reset_index(drop=True)
    df = df[df["大会"]!="ＪＯＭＯ　ＣＵＰ"].reset_index(drop=True)
    df = df[df["大会"]!="スペシャルマッチ"].reset_index(drop=True)
    df = df[df["大会"]!="明治安田ワールドチャレンジ"].reset_index(drop=True)
    return df

def _processing_rename_team(df):
    """
    チーム名について、同じ意味だが表記の異なるデータを書き換える
    """
    def _rename_team(df, old, new):
        df["ホーム"] = df["ホーム"].replace(old,new)
        df["アウェイ"] = df["アウェイ"].replace(old,new)
        return df

    df = _rename_team(df, "Ｖ川崎", "東京Ｖ")
    df = _rename_team(df, "横浜M", "横浜FM")
    df = _rename_team(df, "市原", "千葉")
    df = _rename_team(df, "Ｆ東京", "FC東京")
    df = _rename_team(df, "平塚", "湘南")
    df = _rename_team(df, "B仙台", "仙台")
    df = _rename_team(df, "草津", "群馬")
    return df

def _processing_rename_studium(df):
    """
    スタジアム名について、同じ意味だが表記の異なるデータを書き換える
    """
    def _rename_studium(df, old, new):
        df["スタジアム"] = df["スタジアム"].replace(old,new)
        return df
    df = _rename_studium(df, "札幌", "札幌ド")
    df = _rename_studium(df, "仙台", "ユアスタ")
    df = _rename_studium(df, "東京", "味スタ")
    df = _rename_studium(df, "平塚", "ＢＭＷス")
    df = _rename_studium(df, "日本平", "アイスタ")
    df = _rename_studium(df, "アウスタ", "アイスタ")
    df = _rename_studium(df, "静岡", "エコパ")
    df = _rename_studium(df, "磐田", "ヤマハ")
    df = _rename_studium(df, "瑞穂陸", "パロ瑞穂")
    df = _rename_studium(df, "長居", "ヤンマー")
    df = _rename_studium(df, "神戸中央", "ノエスタ")
    df = _rename_studium(df, "神戸ウイ", "ノエスタ")
    df = _rename_studium(df, "ホムスタ", "ノエスタ")
    df = _rename_studium(df, "ホームズ", "ノエスタ")
    df = _rename_studium(df, "広島ビ", "Ｅスタ")
    df = _rename_studium(df, "鳥栖", "ベアスタ")
    df = _rename_studium(df, "長崎県立", "トラスタ")
    df = _rename_studium(df, "山形県", "ＮＤスタ")
    df = _rename_studium(df, "水戸", "Ｋｓスタ")
    df = _rename_studium(df, "大宮", "ＮＡＣＫ")
    df = _rename_studium(df, "西が丘", "味フィ西")
    df = _rename_studium(df, "三ツ沢", "ニッパツ")
    df = _rename_studium(df, "ニッパ球", "ニッパツ")
    df = _rename_studium(df, "小瀬", "ＮＤスタ")
    df = _rename_studium(df, "新潟ス", "デンカＳ")
    df = _rename_studium(df, "東北電ス", "デンカＳ")
    df = _rename_studium(df, "岡山", "Ｃスタ")
    df = _rename_studium(df, "カンスタ", "Ｃスタ")
    df = _rename_studium(df, "丸亀", "ピカスタ")
    df = _rename_studium(df, "鳴門", "鳴門大塚")
    df = _rename_studium(df, "愛媛陸", "ニンスタ")
    df = _rename_studium(df, "博多球", "レベスタ")
    df = _rename_studium(df, "熊本", "えがおＳ")
    df = _rename_studium(df, "うまスタ", "えがおＳ")
    df = _rename_studium(df, "大分", "大銀ド")
    df = _rename_studium(df, "九石ド", "大銀ド")
    df = _rename_studium(df, "大分ス", "大銀ド")
    df = _rename_studium(df, "盛岡南", "いわスタ")
    df = _rename_studium(df, "秋田球", "Ａ‐スタ")
    df = _rename_studium(df, "福島", "とうスタ")
    df = _rename_studium(df, "群馬陸", "正田スタ")
    df = _rename_studium(df, "南長野", "長野Ｕ")
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
    return pd.DataFrame(ast.literal_eval(tbl))

def fl_get_lost_pattern(competition=1, year=2018):
    """
    失点パターンの取得
    """
    url = "http://www.football-lab.jp/summary/team_ranking/j" + str(competition) + "/?year=" + str(year) + "&data=lost"
    response = requests.get(url)
    bs = BeautifulSoup(response.content,"lxml")
    test=str(bs.find(string=re.compile("function drawChart")))
    tbl = re.search(r'arrayToDataTable\((.*?)\)', test, flags=re.DOTALL|re.MULTILINE).group(1)
    return pd.DataFrame(ast.literal_eval(tbl))

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
