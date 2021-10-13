#package installs
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
import requests
import unidecode
import re



def statScraper(name, year, playerindex, team, team_ids):
    y = 0
    while True:
        checker = 0
        playerindexint = 1 + y
        playerindex = '0' + str(playerindexint)
        for x in range(2):
            url, advanced = urlConvertor(name, year, playerindex, x)
            try:
                result = requests.get(url)
                src = result.content
                soup = BeautifulSoup(src, 'lxml')
                table = soup.find('table', {'class': 'row_summable'})
                trs = table.find_all('tr')
                rows = []
                for tr in trs:
                    tds = tr.find_all('td')
                    row = [td.text.replace('\n', '').strip() for td in tds]
                    rows.append(row)
                if x == 0:
                    columns = ['G', 'Date', 'Age', 'Tm', 'Location', 'Opp',
                               'GS', 'Active', 'MP', 'FG', 'FGA', 'FG%',
                               '3P', '3PA', '3P%', 'FT', 'FTA', 'FT%', 'ORB',
                               'DRB', 'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF',
                               'PTS', 'GmSc', '+/-']
                    df = pd.DataFrame(rows, columns=columns)
                    df = df[df['Tm'] == team_ids[team][0]]
                    result.close()
                    df['PlayerID'] = name[2]
                    df['TmID'] = team_ids[team][1]
                elif x == 1:
                    columns = ['G', 'Date', 'Age', 'Tm', 'Location', 'Opp', 'GS',
                               'Active', 'MP', 'TS%', 'eFG%', 'ORB%', 'DRB%',
                               'TRB%', 'AST%', 'STL%', 'BLK%', 'TOV%',
                               'USG%', 'ORtg', 'DRtg', 'GmSc', 'BPM']
                    df2 = pd.DataFrame(rows, columns=columns)
                    df2 = df2[df2['Tm'] == team_ids[team][0]]
                    result.close()
                    df2 = df2.drop(df2.columns[[0, 2, 3, 4, 5, 6, 7, 8, -2]], axis=1)
            except:
                if y > 4:
                    print('Stat scraping failed for:', name[0], name[1])
                    return None
                y+=1
                checker = 1
                break
        if checker == 0:
            try:
                if len(df) > 0:
                    statdf = pd.merge(df, df2,how='outer', on='Date')
                    statdf.insert(0, 'Name', name[1] + ', ' + name[0])
                    print('Successfully Scraped:', name[0], name[1])
                    return statdf
                else:
                    if y > 4:
                        print('Stat scraping failed for:', name[0], name[1])
                        return None
                    y+=1
            except:
                if y > 4:
                    print('Stat scraping failed for:', name[0], name[1])
                    return None
                y+=1





def urlConvertor(name, year, playerindex, advanced: bool):
    lname = name[1]
    fname = name[0]
    lnamelist = list(lname)
    linitial = lnamelist[0]
    fnamelist = list(fname)
    lname5 = ''
    for x in range(5):
        try:
            lname5 += lnamelist[x]
        except:
            break
    f2i = fnamelist[0] + fnamelist[1]
    if advanced == False:
        url = f'https://www.basketball-reference.com/players/{linitial}/{lname5}{f2i}{playerindex}/gamelog/{year}/'
    else:
        url = f'https://www.basketball-reference.com/players/{linitial}/{lname5}{f2i}{playerindex}/gamelog-advanced/{year}/'
    return url, advanced




def rosterScraper(TeamID, year, id_number):
    url = f"https://www.basketball-reference.com/teams/{TeamID}/{year}.html"
    result = requests.get(url)
    try:
        src = result.content
        soup = BeautifulSoup(src, 'lxml')
        table = soup.find('table', {'class': 'sortable'})
        names = []
        trs = table.find_all('tr')
        rows = []
        for tr in trs:
            try:
                td = tr.find('td', {'data-stat': 'player'})
                a_tag = td.find('a')
                name = a_tag.get_text()
                name = unidecode.unidecode(name)
                name = re.sub(r'[^\w\s]','',name)
                names.append(name)
            except:
                pass
        for x in range(len(names)):
            names[x] = names[x].split()
            names[x].append(id_number)
            id_number += 1
        print(TeamID,"roster successfully parsed")
        return names
    except:
        return False





def teamFinder(year):
    team_id = 101
    url = f"https://www.basketball-reference.com/leagues/NBA_{year}.html"
    result = requests.get(url)
    src = result.content
    soup = BeautifulSoup(src, 'lxml')
    table = soup.find('table', {'class': 'stats_table sortable', 'data-cols-to-freeze': ',2', 'id': 'per_game-team'})
    teams = []
    ids = {}
    trs = table.find_all('tr')
    x = 0
    for tr in trs[1:]:
        #print(tr.prettify())
        try:
            td = tr.find('td', {'data-stat': 'team', 'class': 'left'})
            a_tag = td.find('a')
            team = a_tag.get_text()
            teams.append(team)
            link = a_tag.attrs['href']
            link = list(link)
            acronym = link[7] + link[8] + link[9]
            ids[teams[x]] = []
            ids[teams[x]].append(acronym)
            x+=1
        except:
            pass
    for x in range(len(teams)):
        ids[teams[x]].append(team_id)
        team_id+=1
    return teams, ids



def leagueRosters(year):
    teamrosters = {}
    id_number = 1001
    teams, team_ids = teamFinder(year)
    for team in teams:
        teamrosters[team] = rosterScraper(team_ids[team][0], year, id_number)
        id_number+=len(teamrosters[team])
    return teamrosters, team_ids



def teamRoster(team, year):
    roster = []
    id_number = 1001
    teams, team_ids = teamFinder(year)
    roster = rosterScraper(team_ids[team][0], year, id_number)
    return roster, team_ids




def playerScraper(name, team, year):
    name = name.split()
    name.append('1001')
    teams, team_ids = teamFinder(year)
    df = statScraper(name, year, '01', team, team_ids)
    return df




def teamScraper(team, year):
    roster, team_ids = teamRoster(team, year)
    for x in range(len(roster)):
        try:
            if x == 0:
                player = roster[x]
                df = statScraper(player, year, '01', team, team_ids)
            else:
                player = roster[x]
                df2 = statScraper(player, year, '01', team, team_ids)
                df = df.append(df2)
        except:
            pass
    return df



def leagueScraper(year):
    rosters, team_ids = leagueRosters(year)
    y = 0
    for team in rosters:
        for x in range(len(rosters[team])):
            try:
                if x == 0 and y == 0:
                    player = rosters[team][x]
                    df = statScraper(player, year, '01', team, team_ids)
                else:
                    player = rosters[team][x]
                    df = df.append(statScraper(player, year, '01', team, team_ids))
            except:
                pass
        print(team, 'successfully scraped')
        y+=1
    return df



def save_df(df, title, path):
    df.to_csv(rf'{path}\{title}.csv', index=False)




def csv_to_df(csv):
    return(pd.read_csv(csv))


def clean_stats(df):
    df['GmID'] = 0
    df['WL'] = 0
    for x in range(len(df)):
        #Date
        date = df.loc[x, 'Date']
        date = list(date)
        newdate = ''
        for y in range(10):
            if date[y] != '-':
                newdate+=date[y]
        df.at[x, 'Date'] = float(newdate)

        #Age
        age = df.loc[x, 'Age']
        age = list(age)
        newage = ''
        for y in range(6):
            if age[y] != '-':
                newage+=age[y]
        df.at[x, 'Age'] = float(newage)

        #Location
        location = df.loc[x, 'Location']
        if location == '@':
            df.at[x, 'Location'] = 0
        else:
            df.at[x, 'Location'] = 1

        #GS
        gs = df.loc[x, 'GS']
        gs = list(gs)
        newgs = ''
        if len(gs) == 6:
            newgs = gs[-2]
        else:
            newgs = gs[-3] + gs[-2]
        newgs = float(newgs)
        if gs[0] == 'L':
            newgs = newgs * -1
        df.at[x, 'GS'] = newgs

        #Active
        if df.loc[x, 'Active'] == '0' or df.loc[x, 'Active'] == '1':
            df.at[x, 'Active'] = 1
        else:
            df.at[x, 'Active'] = 0

        #MP
        mp = df.loc[x, 'MP']
        mp = str(mp)
        mp = list(mp)
        newmp = ''
        for y in range(len(mp)):
            if mp[y] != ':':
                newmp+=mp[y]
        newmp = float(newmp)
        df.at[x, 'MP'] = newmp

        #GmID
        date = int(df.loc[x, 'Date'])
        tmID = df.loc[x, 'TmID']
        df.at[x, 'GmID'] = date + tmID

        #WL
        wl = df.loc[x, 'GS']
        if wl > 0:
            df.at[x, 'WL'] = 1
        else:
            df.at[x, 'WL'] = 0
    return df


def standerdize_stats(cleaned_df):
    df_means = cleaned_df.mean()
    df_stdevs = cleaned_df.std()
    normalized_df = cleaned_df
    columns = ['Age', 'GS', 'MP', 'FG', 'FGA', 'FG%', '3P', '3PA', '3P%', 'FT', 'FTA', 'FT%', 'ORB', 'DRB', 'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS', 'GmSc', '+/-', 'TS%', 'eFG%', 'ORB%', 'DRB%', 'TRB%', 'AST%', 'STL%', 'BLK%', 'TOV%', 'USG%', 'ORtg', 'DRtg', 'BPM']
    for column in columns:
        normalized_df[column] = (normalized_df[column] - df_means[column])/df_stdevs[column]
    return normalized_df


def combine_team_stats(df):
    gameids = {}
    for x in range(len(df)):
        if df[x][-1] not in gameids:
            gameids[df[x][-1]] = []
        if df[x][8] == 1:
            gameids[df[x][-1]].append(df[x])
    return gameids



def rid_nans(df):
    df = df.fillna(0)
    return df


def to_numpy(df):
    data = df.to_numpy()
    return data

def save_df(df, title, path):
    df.to_csv(rf'{path}\{title}.csv', index=False)

def get_game_numbers(games):
    numbers = []
    for game in games:
        numbers.append(game)
    return numbers

def game_df(df, gameid):
    df = df[df['GmID'] == gameid]
    return df