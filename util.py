import config
import json
import http.client


def calc_form(state):
    return {
        'win': 3,
        'loss': -1,
        'draw': 1
    }.get(state, 0)


def get_key_by_name(team_name):
    return {
        # Twitter
        'Arsenal': ['#AFC', '#arsenalfc', '#coyg', '#Arsenal'],
        'ManUtd': ['#manutd', '#mufc'],
        'Watford': ['#watfordfc'],
        'Everton': ['#efc'],
        'Newcastle': ['#nufc'],
        'Stoke': ['#scfc'],
        'Leicester': ['#lcfc'],
        'Liverpool': ['#lfc', '#ynwa'],
        'Southampton': '#saintsfc',
        'Swansea': ['#swans', '#swanseacity'],
        'WestBrom': ['#wba', '#westbrom'],
        'Bournemouth': ['#afcb'],
        'CrystalPalace': ['#cpfc'],
        'Huddersfield': ['#huddersfieldfc', '#htafc'],
        'Chelsea': ['#chelsea', '#chelseafc', '#cfc'],
        'Burnley': ['#burnleyfc', '#clarets'],
        'Brighton': ['#bhafc', '#albion'],
        'ManCity': ['#MCFC', '#Mancity'],
        'Tottenham': ['#THFC', '#Spurs', '#coys'],
        'WestHam': ['#Westham', '#hammers', '#whufc']
    }.get(team_name, '#AFC')


def get_tag_by_name(team_name):
    return {
        # Twitter
        'Arsenal': 'Arsenal',
        'ManUtd': 'MUFC',
        'Watford': 'WatfordFC',
        'Everton': 'EFC',
        'Newcastle': 'NUFC',
        'Stoke': 'SCFC',
        'Leicester': 'LCFC',
        'Liverpool': 'LFC',
        'Southampton': 'SaintsFC',
        'Swansea': 'Swans',
        'WestBrom': 'WBA',
        'Bournemouth': 'AFCB',
        'CrystalPalace': 'CPFC',
        'Huddersfield': 'HTAFC',
        'Chelsea': 'CFC',
        'Burnley': 'Clarets',
        'Brighton': 'BHAFC',
        'ManCity': 'MCFC',
        'Tottenham': 'COYS',
        'WestHam': 'WHUFC'
    }.get(team_name, 'AFC')


def get_id_by_name(team_name):
    return {
        # football-data.org
        'Arsenal': 57,
        'ManUtd': 66,
        'Watford': 346,
        'Everton': 62,
        'Newcastle': 67,
        'Stoke': 70,
        'Leicester': 338,
        'Liverpool': 64,
        'Southampton': 340,
        'Swansea': 72,
        'WestBrom': 74,
        'Bournemouth': 1044,
        'CrystalPalace': 354,
        'Huddersfield': 394,
        'Chelsea': 61,
        'Burnley': 328,
        'Brighton': 397,
        'ManCity': 65,
        'Tottenham': 73,
        'WestHam': 563
    }.get(team_name, 57), {
        # Football-API.com
        'Arsenal': 9002,
        'ManUtd': 9260,
        'Watford': 9423,
        'Everton': 9158,
        'Newcastle': 9287,
        'Stoke': 9378,
        'Leicester': 9240,
        'Liverpool': 9249,
        'Southampton': 9363,
        'Swansea': 9387,
        'WestBrom': 9426,
        'Bournemouth': 9053,
        'CrystalPalace': 9127,
        'Huddersfield': 9220,
        'Chelsea': 9092,
        'Burnley': 9072,
        'Brighton': 9065,
        'ManCity': 9259,
        'Tottenham': 9406,
        'WestHam': 9427
    }.get(team_name, 9002), {
        # Football-API.com
        'Arsenal': 18,
        'ManUtd': 2,
        'Watford': 483,
        'Everton': 12,
        'Newcastle': 19,
        'Stoke': 8,
        'Leicester': 481,
        'Liverpool': 1,
        'Southampton': 69,
        'Swansea': 15,
        'WestBrom': 14,
        'Bournemouth': 558,
        'CrystalPalace': 337,
        'Huddersfield': 557,
        'Chelsea': 7,
        'Burnley': 480,
        'Brighton': 482,
        'ManCity': 20,
        'Tottenham': 13,
        'WestHam': 202
    }.get(team_name, 18)


def obtain_opponents(team_id):
    # Comp is 445, status is "TIMED"/"SCHEDULED"
    connection = http.client.HTTPConnection('api.football-data.org')
    headers = {'X-Auth-Token': config.FOOTBALL_DATA_KEY, 'X-Response-Control': 'minified'}
    connection.request('GET', '/v1/teams/' + str(team_id) + '/fixtures?timeFrame=n28', None, headers)
    response = json.loads(connection.getresponse().read().decode())
    return response


def calc_h2h_points(winner, h2h, i, team_id):
    our_score = 0
    opp_score = 0
    draw = 0
    if int(h2h[i]['awayTeam']['dbid']) == team_id:
        if winner == 'home':
            # Our team lost
            our_score += 5 * calc_form('loss')
            opp_score += 5 * calc_form('win')
        elif winner == 'away':
            # We won
            our_score += 5 * calc_form('win')
            opp_score += 5 * calc_form('loss')
        else:
            # Most likely a draw
            draw += 1
    else:  # We are the home team
        if winner == 'away':
            # Our team lost
            our_score += 5 * calc_form('loss')
            opp_score += 5 * calc_form('win')
        elif winner == 'home':
            # We won
            our_score += 5 * calc_form('win')
            opp_score += 5 * calc_form('loss')
        else:
            # Most likely a draw
            draw += 1

    return our_score, opp_score, draw
