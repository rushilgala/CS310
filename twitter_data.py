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


def process_tweets(name, n, query, api):
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
    terms_max = sorted(com_max, key=operator.itemgetter(1), reverse=True)
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


def process_tweet(name):
    with open (os.path.dirname(os.path.abspath(__file__))+'/data/' + name + 'footlytic.json', 'r') as f:
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
        terms_max = sorted(com_max, key=operator.itemgetter(1), reverse=True)
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


def calc_twitter(team, opp):
    # Obtain important identifiers
    team_key_a = util.get_key_by_name(team)
    opp_key_a = util.get_key_by_name(opp)
    team_tag = util.get_tag_by_name(team)
    opp_tag = util.get_tag_by_name(opp)
    max_tweets = 500  # This value could be changed to increase / decrease depending on volume
    api, auth = get_twitter_api_session()
    print('5. twitter calculations...')
    print(api.rate_limit_status()['resources']['search'])
    # Search query is what gets the tweets
    search_query_team = '#'+team_tag+'v'+opp_tag+' OR #'+opp_tag+'v'+team_tag+' OR '+' OR '.join(team_key_a)
    search_query_opp = '#'+team_tag+'v'+opp_tag+' OR #'+opp_tag+'v'+team_tag+' OR '+' OR '.join(opp_key_a)
    # Generate tweet & do calculation
    # DEBUG CODE - writes tweets to file
    # generate_tweets(team, max_tweets, search_query_team, api)
    # generate_tweets(opp, max_tweets, search_query_opp, api)
    # team_pos, team_neg = process_tweet(team)
    # opp_pos, opp_neg = process_tweet(opp)
    team_pos, team_neg = process_tweets(team, max_tweets, search_query_team, api)
    opp_pos, opp_neg = process_tweets(opp, max_tweets, search_query_opp, api)
    # Base case
    our_team = 50 + team_pos + team_neg
    opp_team = 50 + opp_pos + opp_neg
    return our_team, opp_team
