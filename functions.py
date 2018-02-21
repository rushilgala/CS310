import historic_data
import twitter_data
import time
import urllib.request
import json
import http.client
import config
from datetime import datetime
import util


def calc_scores(date, team, opp, isLive):
    team_score_h, opp_score_h, draw_score_h = historic_data.calc_historic(date, team, opp, isLive)
    team_score_t, opp_score_t = twitter_data.calc_twitter(team, opp)

    team_h = team_score_h / (draw_score_h + team_score_h + opp_score_h)
    opp_h = opp_score_h / (draw_score_h + team_score_h + opp_score_h)
    draw_h = draw_score_h / (draw_score_h + team_score_h + opp_score_h)
    team_t = team_score_t / (team_score_t + opp_score_t)
    opp_t = opp_score_t / (team_score_t + opp_score_t)
    return team_h, opp_h, draw_h, team_t, opp_t


def calc_live(team, opp):
    date = datetime.today()
    date = date.strftime('%Y-%m-%d')
    team_h, opp_h, draw_h, team_t, opp_t = calc_scores(date, team, opp, True)
    team_final = (0.15 * team_h) + (0.85 * team_t)
    opp_final = (0.15 * opp_h) + (0.85 * opp_t)
    # Formatting...
    draw_h = '{0:.2f}'.format(float(1 - team_final - opp_final))
    team_final = '{0:.2f}'.format(team_final)
    opp_final = '{0:.2f}'.format(opp_final)
    return team_final, opp_final, draw_h


def calc_future(date, team, opp):
    team_h, opp_h, draw_h, team_t, opp_t = calc_scores(date, team, opp, False)
    team_final = (0.95 * team_h) + (0.05 * team_t)
    opp_final = (0.95 * opp_h) + (0.05 * opp_t)
    # Formatting
    draw_h = '{0:.2f}'.format(draw_h)
    team_final = '{0:.2f}'.format(team_final)
    opp_final = '{0:.2f}'.format(opp_final)

    return team_final, opp_final, draw_h


def get_live_matches():
    today = time.strftime("%Y-%m-%d")
    request_url = 'http://api.football-api.com/2.0/matches?comp_id=1204&team_id=9002%2C9158%2C9423%2C9287%2C9378%2C9260&match_date=' + today + '&Authorization=' + config.FOOTBALL_API_KEY
    try:
        url = urllib.request.Request(request_url)
        data = urllib.request.urlopen(url).read().decode('utf-8', 'ignore')
        data = json.loads(data)
    except urllib.error.URLError as e:
        print('Error getting multiple matches');
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


def get_live_match(team):
    today = time.strftime("%Y-%m-%d")
    test_date = '2018-02-25'
    team_a, team_b, team_c = util.get_id_by_name(team)
    request_url = 'http://api.football-api.com/2.0/matches?comp_id=1204&team_id=' + str(team_b) + '&match_date=' + today + '&Authorization=' + config.FOOTBALL_API_KEY
    try:
        url = urllib.request.Request(request_url)
        data = urllib.request.urlopen(url).read().decode('utf-8', 'ignore')
        data = json.loads(data)
    except urllib.error.URLError as e:
        print('Single live match error');
        data = ''
    except UnicodeEncodeError as e:
        data = ''
    except http.client.BadStatusLine as e:
        data = ''
    except http.client.IncompleteRead as e:
        data = ''
    except urllib.error.HTTPError as e:
        data = ''
    team, opponent, status = '0', '0', '0'
    if data is not '':
        data = data[0]
        status = data['timer']
        if status is '':
            status = '0'
        if data['localteam_id'] == team_b:
            team = data['localteam_score']
            opponent = data['visitorteam_score']
        else:
            team = data['visitorteam_score']
            opponent = data['localteam_score']
        if team is '':
            team = '0'
        if opponent is '':
            opponent = '0'
    return status, team, opponent


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
