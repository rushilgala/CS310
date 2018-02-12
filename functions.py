import historic_data
import twitter_data
import time
import urllib.request
import json
import http.client
import config
from datetime import datetime

import util


def calc_scores(date, team, opp):
    team_score_h, opp_score_h = historic_data.calc_historic(date, team, opp)
    team_score_t, opp_score_t = twitter_data.calc_twitter(team, opp)

    team_h = team_score_h / (team_score_h + opp_score_h)
    opp_h = opp_score_h / (team_score_h + opp_score_h)

    team_t = team_score_t / (team_score_t + opp_score_t)
    opp_t = opp_score_t / (team_score_t + opp_score_t)
    return team_h, opp_h, team_t, opp_t


def calc_live(team, opp):
    date = datetime.today()
    date = date.strftime('%Y-%m-%d')
    team_h, opp_h, team_t, opp_t = calc_scores(date, team, opp)
    team_final = (0.1 * team_h) + (0.9 * team_t)
    opp_final = (0.1 * opp_h) + (0.9 * opp_t)
    # Formatting...
    team_final = '{0:.2f}'.format(team_final)
    opp_final = '{0:.2f}'.format(opp_final)
    return team_final, opp_final


def calc_future(date, team, opp):
    team_h, opp_h, team_t, opp_t = calc_scores(date, team, opp)
    team_final = (0.9 * team_h) + (0.1 * team_t)
    opp_final = (0.9 * opp_h) + (0.1 * opp_t)
    # Formatting
    team_final = '{0:.2f}'.format(team_final)
    opp_final = '{0:.2f}'.format(opp_final)
    return team_final, opp_final


def get_live_matches():
    today = time.strftime("%Y-%m-%d")
    request_url = 'http://api.football-api.com/2.0/matches?comp_id=1204&team_id=9002%2C9158%2C9423%2C9287%2C9378%2C9260&match_date=' + today + '&Authorization=' + config.FOOTBALL_API_KEY
    try:
        url = urllib.request.Request(request_url)
        data = urllib.request.urlopen(url).read().decode('utf-8', 'ignore')
        data = json.loads(data)
    except urllib.error.URLError as e:
        print('http');
        data = ''
    except UnicodeEncodeError as e:
        data = ''
    except http.client.BadStatusLine as e:
        data = ''
    except http.client.IncompleteRead as e:
        data = ''
    except urllib.error.HTTPError as e:
        data = ''
    return data


def get_future_matches(team):
    if team == 'Arsenal':
        myteam = "Arsenal"
        # 9002 team information football-api.com
        id = 57
        opps = util.obtain_opponents(57)
    elif team == 'ManUtd':
        myteam = "Man Utd"
        id = 66
        opps = util.obtain_opponents(66)
    elif team == 'Watford':
        myteam = "Watford"
        id = 346
        opps = util.obtain_opponents(346)
    elif team == 'Everton':
        myteam = "Everton"
        id = 62
        opps = util.obtain_opponents(62)
    elif team == 'Newcastle':
        myteam = "Newcastle"
        id = 67
        opps = util.obtain_opponents(67)
    elif team == 'Stoke':
        myteam = "Stoke City"
        id = 70
        opps = util.obtain_opponents(70)
    else:
        myteam = team
        id = 57
        opps = util.obtain_opponents(57)
    return id, opps, myteam
