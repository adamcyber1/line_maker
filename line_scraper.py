import os
import requests
from bs4 import BeautifulSoup
import datetime
from datetime import date, timedelta
import time
import json

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

"""
A simple script to scrape sports book review for lines. Currently not interecting with the ajax form, needs to be 
added so that more books can be added.
"""

'''
BookID  BookName
238     Pinnacle
19      5Dimes
93      Bookmaker
1096    BetOnline
169     Heritage
123     BetDSI
999996  Bovada
139     Youwager
999991  SIA
43      bet365
92      bodog

'''
DATABASE_PATH = __location__ + '/data/'

BOOKS = {
            'Pinnacle': '238',
            '5Dimes': '19',
            'Bookmaker': '93',
            'BetOnline': '1096',
            'Heritage': '169',
            #'BetDSI': '123',
            #'Bovada': '999996',
            #'Youwager': '139'
        }

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)

def soup_url(type_of_line, tdate = str(date.today()).replace('-','')):
    ## get html code for odds based on desired line type and date
    if type_of_line == 'pointspread':
        url_addon = 'pointspread/'
    elif type_of_line == 'ML':
        url_addon = ''
    elif type_of_line == 'Totals':
        url_addon = 'totals/'
    else:
        raise Exception("Wrong url_addon")

    url = 'https://classic.sportsbookreview.com/betting-odds/nhl-hockey/' + url_addon + '?date=' + tdate
    now = datetime.datetime.now()
    raw_data = requests.get(url)
    soup_big = BeautifulSoup(raw_data.text, 'html.parser')
    soup_list = soup_big.find_all('div', id='OddsGridModule_7')
    if len(soup_list) > 0:
        soup = soup_list[0]
    else:
        soup = None

    timestamp = time.strftime("%H:%M:%S")
    return soup, timestamp

def parse_and_write_data(soup, date, time):
    ## Parse HTML to gather line data by book
    def book_line(book_id, line_id, homeaway):
        ## Get Line info from book ID
        try:
            line = soup.find_all('div', attrs = {'class':'el-div eventLine-book', 'rel':book_id})[line_id].find_all('div')[homeaway].get_text().strip()
            return line
        except Exception:
            return ''

    def score(soup, game_id, homeaway):
        try:
            score = soup.find_all('div', attrs = {'class':'score-content'})[game_id].find_all('span', attrs = {'class': 'total'})[homeaway].get_text().strip()
            return score
        except Exception:
            return ''


    ret = {}
    ret['DATE'] = date
    ret['TIME'] = time

    counter = 0
    number_of_games = len(soup.find_all('div', attrs = {'class':'el-div eventLine-rotation'}))
    games = []
    for i in range(0, number_of_games):
        game = {}
        print(str(i+1)+'/'+str(number_of_games))

        game['HOME'] = soup.find_all('div', attrs = {'class':'el-div eventLine-team'})[i].find_all('div')[0].get_text().strip()
        game['AWAY'] = soup.find_all('div', attrs = {'class':'el-div eventLine-team'})[i].find_all('div')[1].get_text().strip()
        game['HOME_SCORE'] = score(soup, i, 0)
        game['AWAY_SCORE'] = score(soup, i, 1)
        game['HOME_WIN'] = bool(game['HOME_SCORE'] > game['AWAY_SCORE'])

        lines = []
        for book, id in BOOKS.items():
            line = {}

            line['BOOK'] = book
            line['LINE_HOME'] = book_line(id, i, 0)
            line['LINE_AWAY'] = book_line(id, i, 1)
            lines.append(line)

        game["LINES"] = lines
        games.append(game)

    ret["GAMES"] = games
    ret["NMB_GAMES"] = number_of_games

    return ret


def main():

    ## Get today's lines
    #todays_date = str(date.today()).replace('-','')

    ## store BeautifulSoup info for parsing
    #soup_ml, time_ml = soup_url('ML', todays_date)

    ##parse the BeautifulSoup page
    #moneyline = parse_and_write_data(soup_ml, todays_date, time_ml)

    start_date = date(2018, 1, 1)
    end_date = date(2020, 2, 5)
    for single_date in daterange(start_date, end_date):
        date_str = single_date.strftime("%Y%m%d")
        print("Processing date: {}".format(date_str))

        soup, time = soup_url('ML', date_str)
        if soup is None:
            continue
        data = parse_and_write_data(soup, date_str, time)

        with open(DATABASE_PATH + date_str + '.json', 'w') as file:
            json.dump(data, file)

if __name__ == '__main__':
    main()