import util
import http.client
from datetime import datetime, timedelta
import json
import config
import urllib.request
import time


def calc_historic(date, team, opp, isLive):
    # Obtain important identifiers
    team_id_a, team_id_b, team_id_c = util.get_id_by_name(team)
    opp_id_a, opp_id_b, opp_id_c = util.get_id_by_name(opp)
    is_team_home = False  # Set our watched team to false initially, we will do some digging to see
    date = datetime.strptime(date, '%Y-%m-%d')
    # Give each side a base score of 50
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
        # Add 10*(homeWon/AllHomeGames) to home team and 10*(awayWon/allAwayGames) to away team
        # Conditional Probability
        print('2. Getting stats...')
        if is_team_home is True:
            # Team is home, opp is away
            our_team += 10 * int(int(team_data["statistics"][0]["wins_home"]) /
                                 (int(team_data["statistics"][0]["wins_home"]) +
                                  int(team_data["statistics"][0]["draws_home"]) +
                                  int(team_data["statistics"][0]["losses_home"])))
            opp_team += 10 * int(int(opp_data["statistics"][0]["wins_away"]) /
                                 (int(opp_data["statistics"][0]["wins_away"]) +
                                  int(opp_data["statistics"][0]["draws_away"]) +
                                  int(opp_data["statistics"][0]["losses_away"])))
            draw += 2 * int((int(team_data["statistics"][0]["draws_home"]) + int(opp_data["statistics"][0]["draws_away"])) /
                            (int(team_data["statistics"][0]["wins_home"]) +
                            int(team_data["statistics"][0]["draws_home"]) +
                            int(team_data["statistics"][0]["losses_home"])) +
                            int(opp_data["statistics"][0]["wins_away"]) +
                            int(opp_data["statistics"][0]["draws_away"]) +
                            int(opp_data["statistics"][0]["losses_away"]))
        else:
            # opp is home, team is away
            our_team += 10 * int(int(team_data["statistics"][0]["wins_away"]) /
                                 (int(team_data["statistics"][0]["wins_away"]) +
                                  int(team_data["statistics"][0]["draws_away"]) +
                                  int(team_data["statistics"][0]["losses_away"])))
            opp_team += 10 * int(int(opp_data["statistics"][0]["wins_home"]) /
                                 (int(opp_data["statistics"][0]["wins_home"]) +
                                  int(opp_data["statistics"][0]["draws_home"]) +
                                  int(opp_data["statistics"][0]["losses_home"])))
            draw += 2 * int((int(team_data["statistics"][0]["draws_away"]) + int(opp_data["statistics"][0]["draws_home"])) /
                            (int(team_data["statistics"][0]["wins_home"]) +
                            int(team_data["statistics"][0]["draws_home"]) +
                            int(team_data["statistics"][0]["losses_home"])) +
                            int(opp_data["statistics"][0]["wins_away"]) +
                            int(opp_data["statistics"][0]["draws_away"]) +
                            int(opp_data["statistics"][0]["losses_away"]))

        # Use their current position - higher gets more points - 2*(21 - position in league)
        our_team += 2*(21 - int(team_data["statistics"][0]["rank"]))
        opp_team += 2*(21 - int(opp_data["statistics"][0]["rank"]))

        # Live historic data - checking to see if they're likely to score
        if isLive is True:
            today = time.strftime("%Y-%m-%d")
            request_url = 'http://api.football-api.com/2.0/matches?comp_id=1204&team_id=' + str(
                team_id_b) + '&match_date=' + today + '&Authorization=' + config.FOOTBALL_API_KEY
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
            team, opponent, status = 0, 0, 0
            if data is not '':
                data = data[0]
                status = data['timer']
                if status is '':
                    status = 0
                if int(data['localteam_id']) == team_id_b:
                    team = int(data['localteam_score'])
                    opponent = int(data['visitorteam_score'])
                else:
                    team = int(data['visitorteam_score'])
                    opponent = int(data['localteam_score'])
                if team is '':
                    team = 0
                if opponent is '':
                    opponent = 0
                goals_team_total = int(team_data["statistics"][0]["goals"])
                goals_opp_total = int(opp_data["statistics"][0]["goals"])

                if status <= 15:
                    our_team *= ((int(team_data["statistics"][0]["scoring_minutes_0_15_cnt"])/goals_team_total)+1)
                    opp_team *= ((int(opp_data["statistics"][0]["scoring_minutes_0_15_cnt"]) / goals_opp_total) + 1)
                if 15 <= status <= 30:
                    our_team *= ((int(team_data["statistics"][0]["scoring_minutes_15_30_cnt"]) / goals_team_total) + 1)
                    opp_team *= ((int(opp_data["statistics"][0]["scoring_minutes_15_30_cnt"]) / goals_opp_total) + 1)
                if 30 <= status <= 45:
                    our_team *= ((int(team_data["statistics"][0]["scoring_minutes_30_45_cnt"]) / goals_team_total) + 1)
                    opp_team *= ((int(opp_data["statistics"][0]["scoring_minutes_30_45_cnt"]) / goals_opp_total) + 1)
                if 45 <= status <= 60:
                    our_team *= ((int(team_data["statistics"][0]["scoring_minutes_45_60_cnt"]) / goals_team_total) + 1)
                    opp_team *= ((int(opp_data["statistics"][0]["scoring_minutes_45_60_cnt"]) / goals_opp_total) + 1)
                if 60 <= status <= 75:
                    our_team *= ((int(team_data["statistics"][0]["scoring_minutes_60_75_cnt"]) / goals_team_total) + 1)
                    opp_team *= ((int(opp_data["statistics"][0]["scoring_minutes_60_75_cnt"]) / goals_opp_total) + 1)
                if 75 <= status:
                    our_team *= ((int(team_data["statistics"][0]["scoring_minutes_75_90_cnt"]) / goals_team_total) + 1)
                    opp_team *= ((int(opp_data["statistics"][0]["scoring_minutes_75_90_cnt"]) / goals_opp_total) + 1)
    # Obtain data from crowdscores for form and H2H
    DAY = timedelta(1)
    day_from = (date - DAY).strftime('%Y-%m-%dT%H:%M:%S')
    day_to = (date + DAY).strftime('%Y-%m-%dT%H:%M:%S')
    request_url = 'https://api.crowdscores.com/v1/matches?team_id=' + str(team_id_c) + '&from=' + day_from + '&to=' + day_to + '&api_key=' + str(config.CROWD_SCORE_KEY)
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
    except urllib.error.HTTPError as e:
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
    except urllib.error.HTTPError as e:
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

    return our_team, opp_team, draw
