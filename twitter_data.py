import config
import util
import tweepy
import json
import operator
import math
from nltk.corpus import stopwords
import string
from tweepy import AppAuthHandler
import re
import os
import jsonpickle
from collections import Counter
from collections import defaultdict
import time
import urllib.request
import http.client

# Semantic analysis - PMI Approach
positive_vocab = [
    'good', 'nice', 'great', 'awesome', 'outstanding',
    'fantastic', 'terrific', 'well', 'win', 'winning',
    'strong', 'performed', 'goal', 'close', 'possession',
    'shots', 'target', 'linking', 'improved',
]
negative_vocab = [
    'bad', 'terrible', 'crap', 'useless', 'hate', 'disappointing',
    'defeat', 'loss', 'horrible', 'defence', 'poor', 'improving',
    'missing', 'unpopular', 'prick', 'bitter', 'miss', 'blame',
    'piss', 'hostile', 'not good', 'conceed', 'needed', 'failed',
    'frustrating', 'down',
]

neutral_vocab = [
    'draw', 'holding', 'nothing', 'standstill', 'boring', 'nothing'
]
# Other variables
p_t = {}
p_t_com = defaultdict(lambda: defaultdict(int))
com = defaultdict(lambda: defaultdict(int))
pmi = defaultdict(lambda: defaultdict(int))
punctuation = list(string.punctuation)
stop = stopwords.words('english') + punctuation + ['rt', 'via', 'a', 'an', '\'', '...']
regex_str = [
    r'<[^>]+>',  # HTML tags
    r'(?:@[\w_]+)',  # @-mentions
    r"(?:\#+[\w_]+[\w\'_\-]*[\w_]+)",  # hash-tags
    r'http[s]?://(?:[a-z]|[0-9]|[$-_@.&amp;+]|[!*\(\),]|(?:%[0-9a-f][0-9a-f]))+',  # URLs
    r'(?:(?:\d+,?)+(?:\.?\d+)?)',  # numbers
    r"(?:[a-z][a-z'\-_]+[a-z])",  # words with - and '
    r'(?:[\w_]+)',  # other words
    r'(?:\S)'  # anything else
]
tokens_re = re.compile(r'(' + '|'.join(regex_str) + ')', re.VERBOSE | re.IGNORECASE)


def tokenize(s):
    return tokens_re.findall(s)


def preprocess(s, lowercase=False):
    tokens = tokenize(s)
    if lowercase:
        tokens = [token.lower() for token in tokens]
    return tokens


def get_twitter_api_session():
    auth = AppAuthHandler(config.TWITTER_CONSUMER_KEY, config.TWITTER_CONSUMER_SECRET)
    return tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True), auth


def generate_tweets(name, n, query, api):
    with open(os.path.dirname(os.path.abspath(__file__))+'/data/' + name + 'footlytic.json', 'w') as f:
        for tweet in tweepy.Cursor(api.search, q=query, result_type="recent", lang="en").items(n):
            text = tweet._json['text'].lower()
            banned_words = ['rt @', 'stream', 'watch', 'link', 'HD', 'betfair']
            if (not tweet._json['retweeted']) and not any(word in text for word in banned_words):
                f.write(jsonpickle.encode(tweet._json, unpicklable=False) + '\n')


def process_tweets(name, n, query, api, debug):
    count_all = Counter()
    count = 0
    tpq = 100
    while count < n:
        tweets = api.search(q=query, count=tpq, result_type="recent", lang="en")
        for tweet in tweets:
            text = tweet._json['text'].lower()
            banned_words = ['rt @', 'stream', 'watch', 'link', 'HD', 'betfair']
            if (not tweet._json['retweeted']) and not any(word in text for word in banned_words):
                tweet_json = jsonpickle.encode(tweet._json, unpicklable=False)
                tweet = json.loads(tweet_json)
                terms = [term for term in preprocess(tweet['text']) if not term.startswith(('#', '@', name))
                         and len(term) > 2]
                count_all.update(terms)
                # Build co-occurance matrix
                for i in range(len(terms) - 1):
                    for j in range(i + 1, len(terms)):
                        w1, w2 = sorted([terms[i], terms[j]])
                        if w1 != w2:
                            com[w1][w2] += 1
        count += len(tweets)
    com_max = []
    # For each term, look for the most common co-occurrent terms
    for t1 in com:
        t1_max_terms = sorted(com[t1].items(), key=operator.itemgetter(1), reverse=True)[:5]
        for t2, t2_count in t1_max_terms:
            com_max.append(((t1, t2), t2_count))
    # Get the most frequent co-occurrences
    for term, n in count_all.items():
        p_t[term] = n / count
        for t2 in com[term]:
            p_t_com[term][t2] = com[term][t2] / count
    for t1 in p_t:
        for t2 in com[t1]:
            denom = p_t[t1] * p_t[t2]
            pmi[t1][t2] = math.log2(p_t_com[t1][t2] / denom)

    semantic_orientation = {}
    for term, n in p_t.items():
        positive_assoc = sum(pmi[term][tx] for tx in positive_vocab)
        negative_assoc = sum(pmi[term][tx] for tx in negative_vocab)
        
        semantic_orientation[term] = positive_assoc - negative_assoc
    semantic_sorted = sorted(semantic_orientation.items(),
                             key=operator.itemgetter(1),
                             reverse=True)
    top_pos = semantic_sorted[:150]
    top_neg = semantic_sorted[-150:]
    top_neu = semantic_sorted[300:450]
    pos = sum(i[1] for i in top_pos)
    neg = sum(i[1] for i in top_neg)
    neu = sum(i[1] for i in top_neu)
    if debug is True:
        print('Positive tweets: ', top_pos)
        print('Negative tweets: ', top_neg)
        print('Neutral tweets: ', top_neu)
        print('Positive score: ', pos, ' - Negative score: ', neg, ' - Neutral score: ', neu)
    return pos, neg, neu


def process_tweet(name):
    with open(os.path.dirname(os.path.abspath(__file__))+'/data/' + name + 'footlytic.json', 'r') as f:
        count_all = Counter()
        count = 0
        for line in f:
            tweet = json.loads(line)
            count += 1
            terms = [term for term in preprocess(tweet['text']) if not term.startswith(('#', '@', name))
                     and len(term) > 2]
            count_all.update(terms)
            # Build co-occurance matrix
            for i in range(len(terms) - 1):
                for j in range(i + 1, len(terms)):
                    w1, w2 = sorted([terms[i], terms[j]])
                    if w1 != w2:
                        com[w1][w2] += 1
        com_max = []
        # For each term, look for the most common co-occurrent terms
        for t1 in com:
            t1_max_terms = sorted(com[t1].items(), key=operator.itemgetter(1), reverse=True)[:5]
            for t2, t2_count in t1_max_terms:
                com_max.append(((t1, t2), t2_count))
        # Get the most frequent co-occurrences
        for term, n in count_all.items():
            p_t[term] = n / count
            for t2 in com[term]:
                p_t_com[term][t2] = com[term][t2] / count
        for t1 in p_t:
            for t2 in com[t1]:
                denom = p_t[t1] * p_t[t2]
                pmi[t1][t2] = math.log2(p_t_com[t1][t2] / denom)

        semantic_orientation = {}
        for term, n in p_t.items():
            positive_assoc = sum(pmi[term][tx] for tx in positive_vocab)
            negative_assoc = sum(pmi[term][tx] for tx in negative_vocab)
            semantic_orientation[term] = positive_assoc - negative_assoc
        semantic_sorted = sorted(semantic_orientation.items(),
                                 key=operator.itemgetter(1),
                                 reverse=True)
        top_pos = semantic_sorted[:50]
        top_neg = semantic_sorted[-50:]
        pos = sum(i[1] for i in top_pos)
        neg = sum(i[1] for i in top_neg)
        return pos, neg


def calc_twitter(team, opp, is_live, debug):
    # Obtain important identifiers
    team_key_a = util.get_key_by_name(team)
    opp_key_a = util.get_key_by_name(opp)
    team_tag = util.get_tag_by_name(team)
    opp_tag = util.get_tag_by_name(opp)
    _, team_id_b, _ = util.get_id_by_name(team)
    _, _, _ = util.get_id_by_name(opp)
    max_tweets = 750  # This value could be changed to increase / decrease depending on volume
    api, _ = get_twitter_api_session()
    print('5. twitter calculations...')
    print(api.rate_limit_status()['resources']['search'])
    # Search query is what gets the tweets
    search_query_team = '#'+team_tag+' OR '+' OR '.join(team_key_a)
    search_query_opp = '#'+opp_tag+' OR '+' OR '.join(opp_key_a)
    # Generate tweet & do calculation
    # DEBUG CODE - writes tweets to file
    if debug is True:
        generate_tweets(team, max_tweets, search_query_team, api)
        generate_tweets(opp, max_tweets, search_query_opp, api)
        # team_pos, team_neg = process_tweet(team)
        # opp_pos, opp_neg = process_tweet(opp)
    team_pos, team_neg, team_neu = process_tweets(team, max_tweets, search_query_team, api, debug)
    opp_pos, opp_neg, opp_neu = process_tweets(opp, max_tweets, search_query_opp, api, debug)
    # Base case
    our_team = 500 + team_pos + team_neg + team_neu
    opp_team = 500 + opp_pos + opp_neg + opp_neu
    draw = (our_team + opp_team)/2
    # Strengthening the draw position by backing up tweets with live stats
    if is_live is True:
        today = time.strftime("%Y-%m-%d")
        request_url = 'http://api.football-api.com/2.0/matches?comp_id=1204&team_id=' + str(
            team_id_b) + '&match_date=' + today + '&Authorization=' + config.FOOTBALL_API_KEY
        try:
            url = urllib.request.Request(request_url)
            data = urllib.request.urlopen(url).read().decode('utf-8', 'ignore')
            data = json.loads(data)
        except urllib.error.URLError as e:
            print('Single live match error', e)
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
            diff = abs(team - opponent)
            if int(status) > 0:

                if int(status) <= 15:
                    if team == opponent:
                        draw *= 1.1
                    if team < opponent:
                        our_team *= 0.9 * diff
                        opp_team *= 1.1 * diff
                        draw *= 1 * diff
                    if opponent < team:
                        our_team *= 1.1 * diff
                        opp_team *= 0.9 * diff
                        draw *= 1 * diff
                if 15 < int(status) <= 30:
                    if team == opponent:
                        draw *= 1.1
                    if team < opponent:
                        our_team *= 0.9 * diff
                        opp_team *= 1.1 * diff
                        draw *= 1 * diff
                    if opponent < team:
                        our_team *= 1.1 * diff
                        opp_team *= 0.9 * diff
                        draw *= 1 * diff
                if 30 < int(status) <= 45:
                    if team == opponent:
                        draw *= 1.3
                    if team < opponent:
                        our_team *= 0.88 * diff
                        opp_team *= 1.12 * diff
                        draw *= 1 * diff
                    if opponent < team:
                        our_team *= 1.12 * diff
                        opp_team *= 0.88 * diff
                        draw *= 1 * diff
                if 45 < int(status) <= 60:
                    if team == opponent:
                        draw *= 1.4
                    if team < opponent:
                        our_team *= 0.87 * diff
                        draw *= 1 * diff
                        opp_team *= 1.13 * diff
                    if opponent < team:
                        our_team *= 1.13 * diff
                        opp_team *= 0.87 * diff
                        draw *= 1 * diff
                if 60 < int(status) <= 75:
                    if team == opponent:
                        draw *= 1.5
                    if team < opponent:
                        our_team *= 0.86 * diff
                        draw *= 1 * diff
                        opp_team *= 1.14 * diff
                    if opponent < team:
                        our_team *= 1.14 * diff
                        draw *= 1 * diff
                        opp_team *= 0.86 * diff
                if 75 < int(status) <= 87:
                    if team == opponent:
                        draw *= 1.7
                    if team < opponent:
                        our_team *= 0.7 * diff
                        draw *= 1 * diff
                        opp_team *= 1.3 * diff
                    if opponent < team:
                        our_team *= 1.3 * diff
                        draw *= 1 * diff
                        opp_team *= 0.7 * diff
                if 87 <= int(status):
                    if team == opponent:
                        draw *= 3
                    if team < opponent:
                        our_team *= 0.5 * diff
                        opp_team *= 5 * diff
                        draw *= 1 * diff
                    if opponent < team:
                        our_team *= 5 * diff
                        draw *= 1 * diff
                        opp_team *= 0.5 * diff
            # What if we've already played the game...
            if data['status'] == 'FT':
                if int(data['localteam_id']) == team_id_b:
                    team = int(data['localteam_score']) if data['localteam_score'] is not '?' else 0
                    opponent = int(data['visitorteam_score']) if data['visitorteam_score'] is not '?' else 0
                else:
                    team = int(data['visitorteam_score']) if data['visitorteam_score'] is not '?' else 0
                    opponent = int(data['localteam_score']) if data['localteam_score'] is not '?' else 0
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
    if our_team < 0:
        our_team = 0
    if opp_team < 0:
        opp_team = 0
    if draw < 0:
        draw = 0
    if debug is True:
        print('Twitter Scores: ', our_team, ' ', opp_team, ' ', draw)
    return our_team, opp_team, draw
