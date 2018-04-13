import util
import http.client
from datetime import datetime, timedelta
import json
import config
import urllib.request
import time


def calc_historic(date, team, opp, is_live):
    # Obtain important identifiers
    guard = ''
    team_id_a, team_id_b, team_id_c = util.get_id_by_name(team)
    opp_id_a, opp_id_b, _ = util.get_id_by_name(opp)
    is_team_home = False  # Set our watched team to false initially, we will do some digging to see
    date = datetime.strptime(date, '%Y-%m-%d')
    # Give each side a base score
    our_team = 33
    opp_team = 33
    draw = 33
    # Hit the APIs for data
    connection = http.client.HTTPConnection('api.football-api.com')
    connection.request('GET', '/2.0/team/' + str(team_id_b) + '?Authorization=' + str(config.FOOTBALL_API_KEY), None)
    team_data = json.loads(connection.getresponse().read().decode())
    connection.request('GET', '/2.0/team/' + str(opp_id_b) + '?Authorization=' + str(config.FOOTBALL_API_KEY), None)
    opp_data = json.loads(connection.getresponse().read().decode())
    # Find out which team is home and away
    connection = http.client.HTTPConnection('api.football-data.org')
    headers = {'X-Auth-Token': config.FOOTBALL_DATA_KEY, 'X-Response-Control': 'minified'}
    connection.request('GET', '/v1/teams/' + str(team_id_a) + '/fixtures?timeFrame=n28', None, headers)
    data = json.loads(connection.getresponse().read().decode())
    if 'fixtures' in data:
        print('1. Getting fixtures..')
        fixtures = data['fixtures']
        for i in range(0, len(fixtures)):
            date = fixtures[i]['date']
            date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ')
            if int(fixtures[i]['homeTeamId']) == opp_id_a:
                is_team_home = False
                break
            elif int(fixtures[i]['awayTeamId']) == opp_id_a:
                is_team_home = True
                break
            else:
                continue
    if 'statistics' in team_data:
        # Add 40*(homeWon/AllHomeGames) to home team and 10*(awayWon/allAwayGames) to away team
        # Conditional Probability
        print('2. Getting stats...')
        if is_team_home is True:
            # Team is home, opp is away
            our_team += 40 * int(int(team_data["statistics"][0]["wins_home"]) /
                                 (int(team_data["statistics"][0]["wins_home"]) +
                                  int(team_data["statistics"][0]["draws_home"]) +
                                  int(team_data["statistics"][0]["losses_home"])))
            opp_team += 40 * int(int(opp_data["statistics"][0]["wins_away"]) /
                                 (int(opp_data["statistics"][0]["wins_away"]) +
                                  int(opp_data["statistics"][0]["draws_away"]) +
                                  int(opp_data["statistics"][0]["losses_away"])))
            draw += 10 * int((int(team_data["statistics"][0]["draws_home"]) + int(opp_data["statistics"][0]["draws_away"])) /
                            (int(team_data["statistics"][0]["wins_home"]) +
                            int(team_data["statistics"][0]["draws_home"]) +
                            int(team_data["statistics"][0]["losses_home"])) +
                            int(opp_data["statistics"][0]["wins_away"]) +
                            int(opp_data["statistics"][0]["draws_away"]) +
                            int(opp_data["statistics"][0]["losses_away"]))
        else:
            # opp is home, team is away
            our_team += 40 * int(int(team_data["statistics"][0]["wins_away"]) /
                                 (int(team_data["statistics"][0]["wins_away"]) +
                                  int(team_data["statistics"][0]["draws_away"]) +
                                  int(team_data["statistics"][0]["losses_away"])))
            opp_team += 40 * int(int(opp_data["statistics"][0]["wins_home"]) /
                                 (int(opp_data["statistics"][0]["wins_home"]) +
                                  int(opp_data["statistics"][0]["draws_home"]) +
                                  int(opp_data["statistics"][0]["losses_home"])))
            draw += 10 * int((int(team_data["statistics"][0]["draws_away"]) + int(opp_data["statistics"][0]["draws_home"])) /
                            (int(team_data["statistics"][0]["wins_home"]) +
                            int(team_data["statistics"][0]["draws_home"]) +
                            int(team_data["statistics"][0]["losses_home"])) +
                            int(opp_data["statistics"][0]["wins_away"]) +
                            int(opp_data["statistics"][0]["draws_away"]) +
                            int(opp_data["statistics"][0]["losses_away"]))

        # Use their current position - higher gets more points - 2*(21 - position in league)
        our_team += 20*(21 - int(team_data["statistics"][0]["rank"]))
        opp_team += 20*(21 - int(opp_data["statistics"][0]["rank"]))

        # Live historic data - checking to see if they're likely to score
        if is_live is True:
            today = time.strftime("%Y-%m-%d")
            request_url = 'http://api.football-api.com/2.0/matches?comp_id=1204&team_id=' + str(
                team_id_b) + '&match_date=' + today + '&Authorization=' + config.FOOTBALL_API_KEY
            try:
                url = urllib.request.Request(request_url)
                data = urllib.request.urlopen(url).read().decode('utf-8', 'ignore')
                data = json.loads(data)
                guard = data[0]
            except urllib.error.URLError as e:
                print('Single live match error')
                data = ''
            except UnicodeEncodeError as e:
                data = ''
            except http.client.BadStatusLine as e:
                data = ''
            except http.client.IncompleteRead as e:
                data = ''
            team, opponent, status = 0, 0, 0
            if data is not '':
                data = data[0]
                status = data['timer']
                if status is '':
                    status = 0
                if status == '90+':
                    status = 90
                if status == '45+':
                    status = 45
                if int(data['localteam_id']) == team_id_b:
                    team = int(data['localteam_score']) if data['localteam_score'] is not '?' else 0
                    opponent = int(data['visitorteam_score']) if data['visitorteam_score'] is not '?' else 0
                else:
                    team = int(data['visitorteam_score']) if data['visitorteam_score'] is not '?' else 0
                    opponent = int(data['localteam_score']) if data['localteam_score'] is not '?' else 0
                if team is '':
                    team = 0
                if opponent is '':
                    opponent = 0
                goals_team_total = int(team_data["statistics"][0]["goals"])
                goals_opp_total = int(opp_data["statistics"][0]["goals"])
                diff = abs(team - opponent)
                if int(status) > 0:
                    if int(status) <= 15:
                        if team == opponent:
                            draw *= 1.2
                        if team < opponent:
                            our_team *= 0.5 * diff
                            opp_team *= 1.2 * diff
                            draw *= diff
                        if opponent < team:
                            our_team *= 1.2 * diff
                            opp_team *= 0.5 * diff
                            draw *= diff
                        our_team *= ((int(team_data["statistics"][0]["scoring_minutes_0_15_cnt"])/goals_team_total)+1)
                        opp_team *= ((int(opp_data["statistics"][0]["scoring_minutes_0_15_cnt"]) / goals_opp_total) + 1)
                    if 15 <= int(status) <= 30:
                        if team == opponent:
                            draw *= 1.3
                        if team < opponent:
                            our_team *= 0.8 * diff
                            opp_team *= 1.3 * diff
                            draw *= diff
                        if opponent < team:
                            our_team *= 1.3 * diff
                            opp_team *= 0.8 * diff
                            draw *= diff
                        our_team *= ((int(team_data["statistics"][0]["scoring_minutes_15_30_cnt"]) / goals_team_total) + 1)
                        opp_team *= ((int(opp_data["statistics"][0]["scoring_minutes_15_30_cnt"]) / goals_opp_total) + 1)
                    if 30 <= int(status) <= 45:
                        if team == opponent:
                            draw *= 1.35
                        if team < opponent:
                            our_team *= 0.8 * diff
                            opp_team *= 1.4 * diff
                            draw *= diff
                        if opponent < team:
                            our_team *= 1.4 * diff
                            opp_team *= 0.8 * diff
                            draw *= diff
                        our_team *= ((int(team_data["statistics"][0]["scoring_minutes_30_45_cnt"]) / goals_team_total) + 1)
                        opp_team *= ((int(opp_data["statistics"][0]["scoring_minutes_30_45_cnt"]) / goals_opp_total) + 1)
                    if 45 <= int(status) <= 60:
                        if team == opponent:
                            draw *= 1.4
                        if team < opponent:
                            our_team *= 0.7 * diff
                            opp_team *= 1.6 * diff
                            draw *= diff
                        if opponent < team:
                            our_team *= 1.6 * diff
                            opp_team *= 0.7 * diff
                            draw *= diff
                        our_team *= ((int(team_data["statistics"][0]["scoring_minutes_45_60_cnt"]) / goals_team_total) + 1)
                        opp_team *= ((int(opp_data["statistics"][0]["scoring_minutes_45_60_cnt"]) / goals_opp_total) + 1)
                    if 60 <= int(status) <= 75:
                        if team == opponent:
                            draw *= 1.45
                        if team < opponent:
                            our_team *= 0.6 * diff
                            opp_team *= 1.8 * diff
                            draw *= diff
                        if opponent < team:
                            our_team *= 1.8 * diff
                            opp_team *= 0.6 * diff
                            draw *= diff
                        our_team *= ((int(team_data["statistics"][0]["scoring_minutes_60_75_cnt"]) / goals_team_total) + 1)
                        opp_team *= ((int(opp_data["statistics"][0]["scoring_minutes_60_75_cnt"]) / goals_opp_total) + 1)
                    if 75 <= int(status) <= 87:
                        if team == opponent:
                            draw *= 1.6
                        if team < opponent:
                            our_team *= 0.5 * diff
                            opp_team *= 2 * diff
                            draw *= diff
                        if opponent < team:
                            our_team *= 2 * diff
                            opp_team *= 0.5 * diff
                            draw *= diff
                        our_team *= ((int(
                            team_data["statistics"][0]["scoring_minutes_75_90_cnt"]) / goals_team_total) + 1)
                        opp_team *= (
                                    (int(opp_data["statistics"][0]["scoring_minutes_75_90_cnt"]) / goals_opp_total) + 1)
                    if 87 <= int(status):
                        if team == opponent:
                            draw *= 3
                        if team < opponent:
                            our_team *= 0.5 * diff
                            opp_team *= 5 * diff
                            draw *= diff
                        if opponent < team:
                            our_team *= 5 * diff
                            opp_team *= 0.5 * diff
                            draw *= diff
                        our_team *= ((int(
                            team_data["statistics"][0]["scoring_minutes_75_90_cnt"]) / goals_team_total) + 1)
                        opp_team *= (
                                    (int(opp_data["statistics"][0]["scoring_minutes_75_90_cnt"]) / goals_opp_total) + 1)
    # Obtain data from crowdscores for form and H2H
    DAY = timedelta(1)
    day_from = (date - DAY).strftime('%Y-%m-%dT%H:%M:%S')
    day_to = (date + DAY).strftime('%Y-%m-%dT%H:%M:%S')
    request_url = 'https://api.crowdscores.com/v1/matches?team_id=' + str(team_id_c) + '&from=' + day_from + '&to=' + day_to + '&api_key=' + str(config.CROWD_SCORE_KEY)
    if config.DEBUG is True:
        print(request_url)
    try:
        url = urllib.request.Request(request_url)
        data = urllib.request.urlopen(url).read().decode('utf-8', 'ignore')
        data = json.loads(data)
    except urllib.error.URLError as e:
        print(e + ': Match ID error')
        data = ''
    except UnicodeEncodeError as e:
        data = ''
    except http.client.BadStatusLine as e:
        data = ''
    except http.client.IncompleteRead as e:
        data = ''
    if data is not '':
        print('3. Getting match id...')
        match_id = data[0]['dbid']
        request_url = 'https://api.crowdscores.com/v1/matches/' + str(match_id) + '/additional-data?api_key=' + str(config.CROWD_SCORE_KEY)
    try:
        url = urllib.request.Request(request_url)
        data = urllib.request.urlopen(url).read().decode('utf-8', 'ignore')
        data = json.loads(data)
    except urllib.error.URLError as e:
        print(e + ': Form and h2h error')
        data = ''
    except UnicodeEncodeError as e:
        data = ''
    except http.client.BadStatusLine as e:
        data = ''
    except http.client.IncompleteRead as e:
        data = ''
    # Last 5 form
    # 2 variables - (a) how recent (b) W/D/L
    # Most recent game: 5 * (W=3, D=1, L=-1) + 4 * (W=3,D=1,L=-1) ...
    if data is not '':
        print('4. Working out form and h2h...')
        home_form = data['additionalStats']['home']['form']
        away_form = data['additionalStats']['away']['form']
        for i in range(0, 5):
            if home_form[i] == 'draw':
                draw += 5 - int(i)
            if away_form[i] == 'draw':
                draw += 5 - int(i)

            if is_team_home is True:
                our_team += (5 - int(i)) * int(util.calc_form(home_form[i]))
                opp_team += (5 - int(i)) * int(util.calc_form(away_form[i]))
            else:
                our_team += (5 - int(i)) * int(util.calc_form(away_form[i]))
                opp_team += (5 - int(i)) * int(util.calc_form(home_form[i]))
        # H2H last (2) game - same as before but carries weight of 10 then 5
        h2h = data['headToHead']
        if len(h2h) > 1:
            winner0 = h2h[0]['outcome']['winner']
            winner1 = h2h[1]['outcome']['winner']
            our_score0, opp_score0, draw0 = util.calc_h2h_points(winner0, h2h, 0, team_id_c)
            our_score1, opp_score1, draw1 = util.calc_h2h_points(winner1, h2h, 1, team_id_c)
            our_team += our_score0 + our_score1
            opp_team += opp_score0 + opp_score1
            draw += draw0 + draw1
        elif len(h2h) > 0:
            winner = h2h[0]['outcome']['winner']
            our_score, opp_score, draw_score = util.calc_h2h_points(winner, h2h, 0, team_id_c)
            our_team += our_score
            opp_team += opp_score
            draw += draw_score
        else:
            our_team += 0
            opp_team += 0
            # Can't do anything as they have never played each other
    # What if we've already played the game...
    if guard is not '' and guard['status'] == 'FT' and is_live is True:
        if int(guard['localteam_id']) == team_id_b:
            team = int(guard['localteam_score']) if guard['localteam_score'] is not '?' else 0
            opponent = int(guard['visitorteam_score']) if guard['visitorteam_score'] is not '?' else 0
        else:
            team = int(guard['visitorteam_score']) if guard['visitorteam_score'] is not '?' else 0
            opponent = int(guard['localteam_score']) if guard['localteam_score'] is not '?' else 0
        if team == opponent:
            draw = 1
            our_team = 0
            opp_team = 0
        if team < opponent:
            draw = 0
            our_team = 0
            opp_team = 1
        if opponent < team:
            draw = 0
            our_team = 1
            opp_team = 0
    return our_team, opp_team, draw
