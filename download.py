import pandas as pd
import sqlite3
import os

DB_FOLDER = "data"
DB_NAME = "jleague.db"

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
    
def download_all_results():
    """
    Jリーグの公式記録ページから、勝敗記録を取得し、SQLite3データベース化する。
    1992年～2017年のデータを取得
    """
    result = pd.DataFrame()
    for year in range(1992,2018):
        df = download_result(year)
        result = pd.concat([result, df])
    
    db_name = DB_FOLDER + '/' + DB_NAME
    if os.path.exists(DB_FOLDER) == False:
        os.mkdir(DB_FOLDER)
    conn = sqlite3.connect(db_name) # DB接続
    result.to_sql("result", conn, if_exists='replace') # DFをDBに変換