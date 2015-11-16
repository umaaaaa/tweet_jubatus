#!/usr/bin/env python
# coding: utf-8

host = '127.0.0.1'
port = 9199
name = 'test2'

import sys
import json
import random
import jubatus
from jubatus.common import Datum
from search import SearchTweets

searchtweets = SearchTweets()

def predict(client):
    count = 0
    dic = {} 
    dic = searchtweets.get_tweet()
    data = []

    for line in dic:
        tweet = dic[line]
        data.append((Datum({'tweet':tweet})))

    for d in data :
        res = client.classify([d])
        # get the predicted shogun name
        sys.stdout.write(max(res[0], key=lambda x: x.score).label)
        sys.stdout.write(' ')
        sys.stdout.write(d.string_values[0][1].encode('utf-8'))
        sys.stdout.write('\n')

if __name__ == '__main__':
    # connect to the jubatus
    client = jubatus.Classifier(host, port, name)
    predict(client)
