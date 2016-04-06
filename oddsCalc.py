#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import urllib2
from datetime import datetime
import math

def get_data(url):
    return json.load(urllib2.urlopen(url))

def calculate_avg_goals(standings):
    total_home_goals = 0.0
    total_away_goals = 0.0
    total_home_games = 0.0
    total_away_games = 0.0
    for team in standings:
        home_goals = team['home']['goals'] * 1.0
        home_goals_against = team['home']['goalsAgainst'] * 1.0
        home_games = team['home']['wins'] + team['home']['draws'] + team['home']['losses']
        avg_home_goals = home_goals/home_games
        avg_home_goals_against = home_goals_against/home_games
        team['home'][u'goalsAverage'] = avg_home_goals
        team['home'][u'goalsAgainstAverage'] = avg_home_goals_against

        away_goals = team['away']['goals'] * 1.0
        away_goals_against = team['away']['goalsAgainst'] * 1.0
        away_games = team['away']['wins'] + team['away']['draws'] + team['away']['losses']
        avg_away_goals = away_goals/away_games
        avg_away_goals_against = away_goals_against/away_games
        team['away'][u'goalsAverage'] = avg_away_goals
        team['away'][u'goalsAgainstAverage'] = avg_away_goals_against

        total_home_goals += home_goals
        total_away_goals += away_goals
        total_home_games += home_games
        total_away_games += away_games

    return total_home_goals/total_home_games, total_away_goals/total_away_games, standings

def get_fixtures_by_match_day(data, match_day):
    return sorted([f for f in data['fixtures'] if f['matchday'] == match_day],
            key=lambda f: f['date'])

def poisson_probability(actual, mean):
    # naive:   math.exp(-mean) * mean**actual / factorial(actual)
    # iterative, to keep the components from getting too large or small:
    p = math.exp(-mean)
    for i in xrange(actual):
        p *= mean
        p /= i+1
    return p

def calculate_odds(avg_home_goals_season, avg_away_goals_season, home_team, away_team):
    # Attack factor for home team
    home_attack_factor = home_team['home']['goalsAverage'] * 1.0/avg_home_goals_season
    #print 'Fator de ataque mandante: {} / {} = {}'.format(home_team['home']['goalsAverage'], avg_home_goals_season, home_attack_factor)
    # Defense factor for away team
    away_defense_factor = away_team['away']['goalsAgainstAverage'] * 1.0/avg_home_goals_season
    #print 'Fator de defesa visitante: {} / {} = {}'.format(away_team['away']['goalsAgainstAverage'], avg_home_goals_season, away_defense_factor)

    # Attack factor for away team
    away_attack_factor = away_team['away']['goalsAverage'] * 1.0/avg_away_goals_season
    #print 'Fator de ataque visitante: {} / {} = {}'.format(away_team['away']['goalsAverage'], avg_away_goals_season, away_attack_factor)
    # Defense factor for home team
    home_defense_factor = home_team['home']['goalsAgainstAverage'] * 1.0/avg_away_goals_season
    #print 'Fator de defesa mandante: {} / {} = {}'.format(home_team['home']['goalsAgainstAverage'], avg_away_goals_season, home_defense_factor)

    # Number of goals to calculate de poisson distribution
    number_goals = range(6)

    # The likely number of goals the home team might score
    home_poisson_avg = home_attack_factor * away_defense_factor * avg_home_goals_season
    home_poisson_dist = [poisson_probability(x, home_poisson_avg) for x in number_goals]
    #print '{}:\t {}'.format(home_team['teamName'].encode('utf-8'), '\t'.join(map(str,home_poisson_dist)))

    # The likely number of goals the away team might score
    away_poisson_avg = away_attack_factor * home_defense_factor * avg_away_goals_season
    away_poisson_dist = [poisson_probability(x, away_poisson_avg) for x in number_goals]
    #print '{}:\t {}'.format(away_team['teamName'].encode('utf-8'), '\t'.join(map(str,away_poisson_dist)))

    # Calculate odds
    home_odds = 0.0
    draw_odds = 0.0
    away_odds = 0.0
    for i in number_goals:
        for j in number_goals:
            if i > j:
                home_odds += home_poisson_dist[i] * away_poisson_dist[j]
            elif i == j:
                draw_odds += home_poisson_dist[i] * away_poisson_dist[j]
            else:
                away_odds += home_poisson_dist[i] * away_poisson_dist[j]

    return 1/home_odds, 1/draw_odds, 1/away_odds




def main():
    base_api = 'http://api.football-data.org/v1/soccerseasons/'
    championship = '394'
    url_league = base_api + championship + '/leagueTable'
    url_fixtures = base_api + championship + '/fixtures'

    # League
    league = get_data(url_league)
    avg_home, avg_away, teams = calculate_avg_goals(league['standing'])
#    print "Media dos gols em casa: {0:.2f}\nMedia dos gols fora de casa {1:.2f}".format(avg_home, avg_away)
#     for team in teams:
#         print team['teamName']
#         print team['home']
#         print team['away']

    # Fixtures
    fixtures = get_data(url_fixtures)
    next_fixtures = get_fixtures_by_match_day(fixtures, league['matchday'])
    fixtures_date = ''
    for fixture in next_fixtures:
        if fixtures_date != fixture['date']:
            fixtures_date = fixture['date']
            print 'Data: {}'.format(fixtures_date)
        print '\t{} v {}'.format(fixture['homeTeamName'].encode('utf-8'), fixture['awayTeamName'].encode('utf-8'))
        home_team = next((t for t in teams if t['teamName'] == fixture['homeTeamName']),None)
        away_team = next((t for t in teams if t['teamName'] == fixture['awayTeamName']),None)
        home_odds, draw_odds, away_odds = calculate_odds(avg_home, avg_away, home_team, away_team)
        print '\t' + '\t'.join(map(str,[home_odds, draw_odds, away_odds]))




if __name__ == '__main__':
    main()
