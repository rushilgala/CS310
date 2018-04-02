import historic_data
import twitter_data
import time
import urllib.request
import json
import http.client
import config
from datetime import datetime
import util


def calc_scores(date, team, opp, is_live):
    team_score_h, opp_score_h, draw_score_h = historic_data.calc_historic(date, team, opp, is_live)
    team_score_t, opp_score_t, draw_score_t = twitter_data.calc_twitter(team, opp, is_live, config.DEBUG)

    team_h = team_score_h / (draw_score_h + team_score_h + opp_score_h)
    opp_h = opp_score_h / (draw_score_h + team_score_h + opp_score_h)
    draw_h = draw_score_h / (draw_score_h + team_score_h + opp_score_h)
    team_t = team_score_t / (draw_score_t + team_score_t + opp_score_t)
    opp_t = opp_score_t / (draw_score_t + team_score_t + opp_score_t)
    draw_t = draw_score_t / (draw_score_t + team_score_t + opp_score_t)
    return team_h, opp_h, draw_h, team_t, opp_t, draw_t


def calc_live(team, opp):
    date = datetime.today()
    date = date.strftime('%Y-%m-%d')
    team_h, opp_h, draw_h, team_t, opp_t, draw_t = calc_scores(date, team, opp, True)
    team_final = (0.3 * team_h) + (0.7 * team_t)
    opp_final = (0.3 * opp_h) + (0.7 * opp_t)
    draw_final = (0.3 * draw_h) + (0.7 * draw_t)
    # Formatting...
    draw_final = '{0:.2f}'.format(draw_final)
    team_final = '{0:.2f}'.format(team_final)
    opp_final = '{0:.2f}'.format(opp_final)
    return team_final, opp_final, draw_final


def calc_future(date, team, opp):
    team_h, opp_h, draw_h, team_t, opp_t, draw_t = calc_scores(date, team, opp, False)
    team_final = (0.9 * team_h) + (0.1 * team_t)
    opp_final = (0.9 * opp_h) + (0.1 * opp_t)
    draw_final = (0.9 * draw_h) + (0.1 * draw_t)
    # Formatting
    draw_final = '{0:.2f}'.format(draw_final)
    team_final = '{0:.2f}'.format(team_final)
    opp_final = '{0:.2f}'.format(opp_final)

    return team_final, opp_final, draw_final


def get_live_matches():
    today = time.strftime("%Y-%m-%d")
    teams = '&team_id=9002%2C9158%2C9423%2C9287%2C9378%2C9260'
    request_url = 'http://api.football-api.com/2.0/matches?comp_id=1204&match_date=' + today + '&Authorization=' + config.FOOTBALL_API_KEY
    try:
        url = urllib.request.Request(request_url)
        data = urllib.request.urlopen(url).read().decode('utf-8', 'ignore')
        data = json.loads(data)
    except urllib.error.URLError as e:
        print('Error getting multiple live matches');
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
    team_a, team_b, team_c = util.get_id_by_name(team)
    request_url = 'http://api.football-api.com/2.0/matches?comp_id=1204&team_id=' + str(team_b) + '&match_date=' + today + '&Authorization=' + config.FOOTBALL_API_KEY
    try:
        url = urllib.request.Request(request_url)
        data = urllib.request.urlopen(url).read().decode('utf-8', 'ignore')
        data = json.loads(data)
    except urllib.error.URLError as e:
        print('Single live match error');
        print(request_url)
        data = ''
    except UnicodeEncodeError as e:
        data = ''
    except http.client.BadStatusLine as e:
        data = ''
    except http.client.IncompleteRead as e:
        data = ''
    except urllib.error.HTTPError as e:
        data = ''
    team, opponent, status, timer = '0', '0', '0', '0'
    if data is not '':
        print(data[0])
        data = data[0]
        timer = data['timer']
        status = data['status']
        if status == 'HT':
            timer = 'HT'
        elif status == 'FT':
            timer = 'FT'
        if timer is '':
            if status is 'HT':
                timer = 'HT'
            elif status is 'FT':
                timer = 'FT'
            else:
                timer = '0'
        if data['localteam_id'] == str(team_b):
            team = data['localteam_score']
            opponent = data['visitorteam_score']
        else:
            team = data['visitorteam_score']
            opponent = data['localteam_score']
        if team is '':
            team = '0'
        if opponent is '':
            opponent = '0'

    return timer, team, opponent


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
