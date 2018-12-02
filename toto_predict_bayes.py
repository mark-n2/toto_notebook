"""
TOTOの予測を行い、結果を返すスクリプト
"""

# パッケージのimport
import download
import process_data
import pandas as pd
import re
import numpy as np

# 内部で使う関数
def get_team_data(team, df):
    """
    指定したチームに関するデータのみ抽出する
    """
    team_data = df[(df["ホーム"]==team) | (df["アウェイ"]==team)]
    return team_data

def get_win_data(team, df, result=3):
    """
    指定したチームが勝利したデータのみ抽出する
    引数resultを指定すると、引き分け/負けのデータも収集可能
    """
    if result == 3:
        win_data = df[((df["ホーム"]==team) & (df["result"]==3)) | ((df["アウェイ"]==team) & (df["result"]==0))]
    elif result == 1:
        win_data = df[(df["result"]==1)]
    elif result == 0:
        win_data = df[((df["ホーム"]==team) & (df["result"]==0)) | ((df["アウェイ"]==team) & (df["result"]==3))]        
    return win_data

def get_studium_data(studium, df):
    """
    指定したスタジアムでのデータのみ抽出する
    """
    studium_data = df[(df["スタジアム"]==studium)]
    return studium_data

def get_month_data(month, df):
    """
    指定した月のデータのみ抽出する
    """
    month_data = df[df["month"]==month]
    return month_data

def proba_all(team, data, index="all"):
    """
    全試合に関する勝率を計算
    """
    team_data = get_team_data(team, data)
    if len(team_data)==0:
        return None
    win_data = get_win_data(team, team_data, result=3)
    draw_data = get_win_data(team, team_data, result=1)
    lose_data = get_win_data(team, team_data, result=0)
    ret = pd.DataFrame()
    ret["win"] = [len(win_data)/len(team_data)]
    ret["draw"] = [len(draw_data)/len(team_data)]
    ret["lose"] = [len(lose_data)/len(team_data)]
    #print(len(win_data),len(draw_data),len(lose_data),len(team_data))
    ret = ret.rename(index={0:index})
    return ret

def proba_oppotunity(team, oppotunity, data):
    """
    対戦相手を限定した際の勝率を計算
    """
    team_data = get_team_data(team, data)
    team_data = get_team_data(oppotunity, team_data)
    return proba_all(team, team_data,index="oppotunity")

def proba_month(team, month, data):
    """
    開催日が何月かで限定した際の勝率を計算
    """
    team_data = get_team_data(team, data)
    month_data = get_month_data(month, team_data)
    #display(month_data)
    return proba_all(team,month_data,index="month")

def proba_quarter(team, month, data):
    """
    開催月を四半期ごとに分けて勝率を計算
    Jリーグはだいたい2月終わり～12月初めまで。12月からは天皇杯。
    """
    QUARTERS = [[1,2,3],[4,5,6],[7,8,9],[10,11,12]]
    if month >= 1 or month <= 3:
        q = 0
    elif month >= 4 and month <= 6:
        q = 1
    elif month >= 7 and month <= 9:
        q = 2
    else:
        q = 3
    team_data = get_team_data(team, data)
    quarter_data = data[(data["month"]==QUARTERS[q][0]) | (data["month"]==QUARTERS[q][1]) | (data["month"]==QUARTERS[q][2])]
    #display(quarter_data)
    return proba_all(team,quarter_data,index="quarter")

def proba_studium(team, studium, data):
    """
    指定スタジアムでの試合に限定した勝率を計算
    """
    team_data = get_team_data(team, data)
    studium_data = get_studium_data(studium, team_data)
    return proba_all(team, studium_data,index="studium")

def prediction(home, away, month, studium, df):
    tmp = pd.DataFrame()
    proba = proba_all(home, df)
    if proba is not None:
        tmp = tmp.append(proba)
    proba = proba_oppotunity(home, away, df)
    if proba is not None:
        tmp = tmp.append(proba)
#    proba = proba_month(home, month, df)
#    if proba is not None:
#        tmp = tmp.append(proba)
    proba = proba_quarter(home, month, df)
    if proba is not None:
        tmp = tmp.append(proba)
    proba = proba_studium(home, studium, df)
    if proba is not None:
        tmp = tmp.append(proba)
    return tmp.product().idxmax(), tmp

# 公開クラス
class toto_predict_bayes:
    def __init__(self):
        # データベースから予想データを収集
        df = download.get_db_data()
        df = process_data.processing_data(df)
        # 符号化処理
        home = pd.concat([df["ホーム"],df["アウェイ"]]).drop_duplicates().reset_index(drop=True).to_dict()
        team_dict = {v:k for k, v in home.items()} # 辞書のキー・バリュー交換
        tmp = [team_dict[df["ホーム"][i]] for i in range(len(df))]
        df["home"] = tmp
        tmp = [team_dict[df["アウェイ"][i]] for i in range(len(df))]
        df["away"] = tmp
        studium = df["スタジアム"].drop_duplicates().reset_index(drop=True).to_dict()
        studium_dict = {v:k for k, v in studium.items()}
        tmp = [studium_dict[df["スタジアム"][i]] for i in range(len(df))]
        df["studium"] = tmp
        wdl = []
        # win-draw-lose VゴールとかPKとかはTOTO予想に関係ないので無視
        LOSE = 0
        DRAW = 1
        WIN = 3
        OTHER = np.nan
        for result in df["スコア"]:
            tmp = re.split("[-()]",result)
            if len(tmp) < 2: # X-Xという形式でないものはスルー
                wdl.append(OTHER)
                continue
            if int(tmp[0]) > int(tmp[1]):
                wdl.append(WIN)
            elif int(tmp[0]) < int(tmp[1]):
                wdl.append(LOSE)
            else:
                wdl.append(DRAW)
        df["result"] = wdl
        month = []
        for match_day in df["試合日"]:
            tmp = match_day.split("/")[0]
            if tmp.isdigit() == True:
                month.append(int(tmp))
            else:
                month.append(np.nan)
        df["month"] = month
        df = df.rename(columns={"年度":"year"})
        # データを保存
        self.df = df
        
    def get_prediction(self, hldCnt):
        """
        本スクリプトのMain
        hldCnt(開催回)を指定し、予想データを返す
        """
        # TOTOの開催情報を収集
        toto, miniA, miniB, goal = download.get_toto_schedule(hldCnt)
        # 予測を行う
        pred_home = []
        pred_away = []
        pred_result = []
        for i in range(len(toto)):
            #print(toto["ホーム"].iloc[i],toto["アウェイ"].iloc[i],int(toto["開催日"].iloc[i].split("/")[0]),toto["競技場"].iloc[i],end="")
            tmp1, tmp2 = prediction(toto["ホーム"].iloc[i],toto["アウェイ"].iloc[i],int(toto["開催日"].iloc[i].split("/")[0]),toto["競技場"].iloc[i],self.df)
            tmp3, tmp4 = prediction(toto["アウェイ"].iloc[i],toto["ホーム"].iloc[i],int(toto["開催日"].iloc[i].split("/")[0]),toto["競技場"].iloc[i],self.df)
            #print(tmp)
            pred_home.append(tmp1)
            pred_away.append(tmp3)
            if pred_home[i] == pred_away[i]:
                pred_result.append("draw")
            elif pred_home[i] == "win" or (pred_home[i] == "draw" and pred_away[i] == "lose"):
                pred_result.append("win")
            else:
                pred_result.append("lose")

        toto["予想1"] = pred_home
        toto["予想2"] = pred_away
        toto["最終予想"] = pred_result
        return toto