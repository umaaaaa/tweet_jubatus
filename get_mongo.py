#usr/bin/env python
# -*- coding:utf-8 -*-

from pymongo import MongoClient
import json

class convert_mongo:
    global true_col
    global false_col
    global col
    con = MongoClient('127.0.0.1', 27017)
    db = con['tweetdb']
    col = db.tweets
    true_col = db.true_collection
    false_col = db.false_collection
    global dic
    dic = {}

    def get_dic(self):
        count = 0
        for data in col.find():
            del data['_id']
            json_list = json.dumps(data)
            dic[count] = json.loads(json_list)
            count += 1
        return dic

    def get_true_dic(self):
        count = 0
        for data in true_col.find():
            del data['_id']
            json_list = json.dumps(data)
            dic[count] = json.loads(json_list)
            count += 1
        return dic

    def get_false_dic(self):
        count = 0
        for data in false_col.find():
            del data['_id']
            json_list = json.dumps(data)
            dic[count] = json.loads(json_list)
            count += 1
        return dic
