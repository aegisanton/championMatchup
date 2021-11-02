# Test for Riot Games API
# Anton Chen

import math
import os
import requests
import json
import pandas as pd
import tkinter as tk
from PIL import Image, ImageTk

API_URL = "api.riotgames.com"
DDRAGON_URL = "https://ddragon.leagueoflegends.com"
API_KEY = ""

# Test variables
SUMMONER = "Aegis"
DF = None

# Tkinter

def selectChamp(idx, champs, root):
    champ = champs[idx]

    #newWindow = tk.Toplevel(root)
    #newWindow.title(champ)
    #newWindow.geometry("200x720")

    getWinRates(champ)    

def setSummoner(name):
    global SUMMONER
    global DF
    SUMMONER = name

    # Check if a file exists for this summoner. If no, download data first
    if not os.path.exists("{}.json".format(SUMMONER)):
        # Get the summoner PUUID and get all normal matches SR
        puuid = getSummonerPUUID(SUMMONER)
        matches = getAllMatches(puuid, "normal", 400) # 400 is SR draft pick 5v5

        data = []

        for i in range(len(matches)):
            m = MatchHandler(matches[i])
            data.append(m.__dict__)

        with open("{}.json".format(SUMMONER), "w") as f:
            json.dump(data, f)

    # Load the data into a dataframe
    DF = pd.read_json("{}.json".format(SUMMONER), orient="records")
    DF = DF.astype({"playerChamp":"category","enemyChamp":"category", "win":"category", "matchID":"string"})
    DF = DF.drop(["matchID"], axis=1)
    DF = DF.pivot_table(index=["playerChamp", "enemyChamp"], columns="win", aggfunc="size", fill_value=0)
    print(DF)

# Pandas

def getWinRates(champ):
    winRate = DF[DF["playerChamp",:] == champ]
    print(winRate)
    
# Help classes

class MatchHandler():
    def __init__(self, matchID):
        self.matchID = matchID

        matchData = self.getMatch()
        self.initialize(matchData)

    def getMatch(self):
        region = "europe"
        url = "https://{}.{}/lol/match/v5/matches/{}".format(region, API_URL, self.matchID)
        headers = {"X-Riot-Token": API_KEY}

        res = requests.get(url, headers=headers)

        if res.status_code == 200:
            return res.json()
        else:
            return

    def initialize(self, data):
        players_data = data["info"].get("participants")
        players = []
        position = ""
        summonerChamp = ""
        enemyChamp = ""
        win = True

        for i in range(len(players_data)):
            player = {"champion": players_data[i].get("championName"),
                      "position": players_data[i].get("individualPosition"),
                      "summoner": players_data[i].get("summonerName"),
                      "win": players_data[i].get("win")
                      }
            if player.get("summoner") == SUMMONER:
                summonerChamp = player.get("champion")
                position = player.get("position")
                win = player.get("win")
            else:
                players.append(player)

        for i in range(len(players)):
            if players[i].get("position") == position:
                enemyChamp = players[i].get("champion")
                break

        self.playerChamp = summonerChamp
        self.enemyChamp = enemyChamp
        self.win = win

    def test(self):
        print(self.__dict__)

class MatchPlayerHandler():
    def __init__(self, puuid):
        self.puuid = puuid

# Riot Games API 

def getSummoner(name):
    server = "euw1"
    url = "https://{}.{}/lol/summoner/v4/summoners/by-name/{}".format(server, API_URL, name)
    headers = {"X-Riot-Token": API_KEY}

    res = requests.get(url, headers=headers)

    if res.status_code == 200:
        return res.json()
    else:
        return

def getSummonerID(name):
    res = getSummoner(name)

    return res.get("id")

def getSummonerPUUID(name):
    res = getSummoner(name)

    return res.get("puuid") 

def getMatches(puuid, gType, qType, start=0, count=100):
    
    region = "europe"
    url = "https://{}.{}/lol/match/v5/matches/by-puuid/{}/ids?type={}&queue={}&start={}&count={}".format(region, API_URL, puuid, gType, qType, start, count)
    headers = {"X-Riot-Token": API_KEY}

    res = requests.get(url, headers=headers)

    if res.status_code == 200:
        return res.json()
    else:
        return

def getAllMatches(puuid, gType, qType):
    index = 0
    count = 100
    matches = []

    while True:
        res = getMatches(puuid, gType, qType, start=index, count=count)
        matches += res
        index += 100

        if len(res) < 100:
            break

    return matches

def getMastery(summ_id):
    region = "europe"
    url = "https://{}.{}/lol/champion-mastery/v4/champion-masteries/by-summoner/{}".format(region, API_URL, summ_id)
    headers = {"X-Riot-Token": API_KEY}

    res = requests.get(url, headers=headers)

    if res.status_code == 200:
        return res.json()
    else:
        return

# Data Dragon

def getLatestVers():
    url = "{}/api/versions.json".format(DDRAGON_URL)

    res = requests.get(url)

    if res.status_code == 200:
        return res.json()[0]
    else:
        return

def getChampionData():
    vers = getLatestVers()
    url = "{}/cdn/{}/data/en_US/champion.json".format(DDRAGON_URL, vers)

    res = requests.get(url)

    if res.status_code == 200:
        return res.json().get("data")
    else:
        return

def getChampionIcons(data):
    vers = getLatestVers()
    icons = []

    for champ in data.keys():
        url = "{}/cdn/{}/img/champion/{}.png".format(DDRAGON_URL, vers, champ)

        res = requests.get(url)

        if res.status_code == 200:
            img = ImageTk.PhotoImage(data=res.content)
            icons.append(img)
        else:
            break

    return icons

# App

def main():
    root = tk.Tk()

    #m = MatchHandler(matches[0])
    champData = getChampionData()
    champIcons = getChampionIcons(champData)

    # Window settings
    root.title("Champion Matchup Analyzer")

    width = 1280
    height = 720
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    center_x = int(screen_width/2 - width/2)
    center_y = int(screen_height/2 - height/2)

    root.geometry(f"{width}x{height}+{center_x}+{center_y}")

    # Grid

    nCols = 10                              # Champions per row
    champCount = len(champData)
    champs = list(champData)
    nRows = math.ceil(champCount / nCols)

    # Input

    tk.Label(root, text="Summoner Name").grid(row=0, column=0)
    entry = tk.Entry(root)
    entry.grid(row=0, column=1)
    tk.Button(root, text="Confirm", command=lambda:setSummoner(entry.get())).grid(row=0, column=2)

    # Buttons

    idx = 0

    for i in range(nRows):
        for j in range(nCols):
            tk.Button(root, image=champIcons[idx], command=lambda k=idx:selectChamp(k, champs, root)).grid(row=i+1, column=j)
            idx += 1

            if idx >= champCount:
                break

    root.mainloop()
    
main()


