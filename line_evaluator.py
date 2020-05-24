"""
A script that ingests the JSON line data produced by line_scraper.py and evaluates the predictive ability of the
bookies / the aggregate of the bookies
"""

import numpy as np
from pandas import DataFrame, concat, Series
from json import loads
from re import match
from math import log
import glob

#supported bookie so far
BOOKIES = ['PINNACLE', '5DIMES', 'BOOKMAKER', 'BETONLINE', 'HERITAGE']

def record_to_dataframe(record: dict):
    df = DataFrame(
        columns=('HOME', 'AWAY', 'HOME_SCORE', 'AWAY_SCORE', 'HOME_WIN',
                 'PINNACLE_LINE_HOME', 'PINNACLE_LINE_AWAY',
                 '5DIMES_LINE_HOME', '5DIMES_LINE_AWAY',
                 'BOOKMAKER_LINE_HOME', 'BOOKMAKER_LINE_AWAY',
                 'BETONLINE_LINE_HOME', 'BETONLINE_LINE_AWAY',
                 'HERITAGE_LINE_HOME', 'HERITAGE_LINE_AWAY',
                 ))

    if record['NMB_GAMES'] == 0:
        return df

    games = record['GAMES']
    for game in games:
        game_row = [game['HOME'], game['AWAY'], game['HOME_SCORE'], game['AWAY_SCORE'], game['HOME_WIN']]



        lines = game["LINES"]
        for line in lines:
            game_row.append(line['LINE_HOME'])
            game_row.append(line['LINE_AWAY'])

        df.loc[len(df)] = game_row

    return df

def combine_dataframes(*args):
    frames = [*args]
    return concat(frames)

def get_best_home_line(game_row: Series):
    best_line = None
    for column in game_row.iteritems():
        if match('.*LINE_HOME$', column[0]):
            if column[1] is not '' and column[1] is not None:
                line = int(column[1])

                if best_line is None:
                    best_line = line
                else:
                    best_line = max(best_line, line)

    return best_line

def get_best_away_line(game_row: Series):
    best_line = None
    for column in game_row.iteritems():
        if match('.*LINE_AWAY$', column[0]):
            if column[1] is not '' and column[1] is not None:
                line = int(column[1])

                if best_line is None:
                    best_line = line
                else:
                    best_line = max(best_line, line)

    return best_line

def add_best_lines(df: DataFrame):
    """
    Adds the best lines for the home and away team. The 'best' line is defined as the line that will give
    the better the maximum return. So basically it is just the 'most positive' moneyline.

    :param df:
    :return:
    """

    df['BEST_LINE_HOME'] = df.apply(get_best_home_line, axis = 1)
    df['BEST_LINE_AWAY'] = df.apply(get_best_away_line, axis = 1)

    return df

# 𝐿𝐿𝑖 = −𝑌𝑖 · ln (S𝑖) + (1 − 𝑌𝑖) · ln (1 − S𝑖).

def probability(moneyline: int):
    #Implied Probability = 100 / (Plus Money-line Odds +100)
    # Implied Probability = (-1 * Minus Money-line Odds) / ((-1 * Minus Money-line Odds)+100))
    if moneyline >= 0:
        return 100 / (moneyline + 100)
    else:
        return (abs(moneyline)) / ((abs(moneyline)) + 100)


def special_log_loss_binary(game_row: Series):
    """
    Calculate the special log loss of the bookies using our custom log loss function.

    The idea is to factor in the 'overround` of the bookies into the log loss calculations That is, the implied
    probability of their favorite and underdog lines add up to >1, yielding them an expected profit.

    :param game_row:
    :return:
    """

    if game_row.BEST_LINE_HOME is None or game_row.BEST_LINE_AWAY is None:
        return None

    home_prob = probability(game_row.BEST_LINE_HOME)
    away_prob = probability(game_row.BEST_LINE_AWAY)
    virtual_home_prob = 1 - away_prob
    virtual_away_prob = 1 - home_prob

    #predicted = favorite_prob
    actual = int(game_row.HOME_WIN)

    # log_likelihood = -1*actual * log(predicted) - (1-actual)*log(1-predicted)

    if actual == 1:
        log_likelihood_adjusted = -1*log(max(home_prob, virtual_home_prob))
    else: # actual == 0
        log_likelihood_adjusted = -1*log(max(away_prob, virtual_away_prob))

    return log_likelihood_adjusted

def basic_log_loss_binary(game_row: Series):
    if game_row.BEST_LINE_HOME is None or game_row.BEST_LINE_AWAY is None:
        return None

    predicted = 0.5 * (probability(game_row.BEST_LINE_HOME) + (1-probability(game_row.BEST_LINE_AWAY)))
    actual = int(game_row.HOME_WIN)

    log_likelihood = -1*actual * log(predicted) - (1-actual)*log(1-predicted)

    return log_likelihood

def add_log_loss(df : DataFrame):
    """
    Apply the log loss function to the bookie odds.
    :param df:
    :return:
    """

    df['BEST_LOG_LOSS'] = df.apply(special_log_loss_binary, axis = 1)
    df['BASIC_LOG_LOSS'] = df.apply(basic_log_loss_binary, axis = 1)

    return df


def main():
    with open("..../data/20180102.json", 'r') as f:
        string = f.read()
        j = loads(string)
        df = record_to_dataframe(j)

        df = add_best_lines(df)
        df = add_log_loss(df)
        print(df)

    df = None
    for filename in glob.glob('....../data/*.json'):

        with open(filename, 'r') as file:
            print(filename)
            current_df = None
            data = file.read()
            j = loads(data)
            current_df = record_to_dataframe(j)
            if current_df.empty:
                continue
            current_df = add_best_lines(current_df)
            current_df = add_log_loss(current_df)

        df = combine_dataframes(df, current_df)

    column_means = df.mean(axis = 0, skipna = True)
    row_means = df.mean(axis = 1, skipna = True)
    print(df)



if __name__ == '__main__':
    main()
