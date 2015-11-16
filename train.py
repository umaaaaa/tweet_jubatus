#!/usr/bin/env python
# coding: utf-8

host = '192.168.33.10'
port = 9199
name = 'test2'

import sys
import json
import random

import jubatus
from jubatus.common import Datum
from get_mongo import convert_mongo 


get_mongo = convert_mongo()

def train(client):
    true_dic = get_mongo.get_true_dic()
    false_dic = get_mongo.get_false_dic()
    train_data = []

    for line in true_dic:
        tweet = true_dic[line]['tweet']
        train_data.append(('true', Datum({'tweet':tweet})))
    for line in false_dic:
        tweet = false_dic[line]['tweet']
        train_data.append(('false', Datum({'tweet':tweet})))

    random.shuffle(train_data)

    client.train(train_data)

if __name__ == '__main__':
    client = jubatus.Classifier(host, port, name)
    train(client)
