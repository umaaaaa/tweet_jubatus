#!/usr/bin/env python
# -*- coding:utf-8 -*-

from requests_oauthlib import OAuth1Session
import json
import time, calendar
import datetime
import locale
import key_dict
from pymongo import MongoClient

oath_key_dict = {
    "consumer_key": key_dict.oath_key_dict['consumer_key'],
    "consumer_secret": key_dict.oath_key_dict['consumer_secret'],
    "access_token": key_dict.oath_key_dict['access_token'],
    "access_token_secret": key_dict.oath_key_dict['access_token_secret']
}

class SearchTweets:

    def YmdHMS(self, created_at):
        st  = time.strptime(created_at, '%a %b %d %H:%M:%S +0000 %Y')
        dt = datetime.datetime(st.tm_year,st.tm_mon,st.tm_mday,st.tm_hour,st.tm_min,st.tm_sec)
        dst = datetime.datetime.strptime(created_at,'%a %b %d %H:%M:%S +0000 %Y')
        # 世界標準時から日本時間にする
        japan_dst = dst + datetime.timedelta(hours=9)
        return japan_dst 

    def get_tweet(self):
        searchtweets = SearchTweets()
        now = datetime.datetime.now()
        now_minus_six = now - datetime.timedelta(hours=6)
        tweets = searchtweets.tweet_search(u"車検 && 辰巳 exclude:retweets exclude:mentions", oath_key_dict)
        tweets_dic = {} 
        count = 0
        
        for tweet in tweets["statuses"]:
            Created_at = searchtweets.YmdHMS(tweet["created_at"])
            tweet_id = tweet[u'id_str']
            text = tweet[u'text']
            created_at = tweet[u'created_at']
            user_id = tweet[u'user'][u'id_str']
            user_description = tweet[u'user'][u'description']
            screen_name = tweet[u'user'][u'screen_name']

            tweets_dic[count] = text
            count += 1

        return tweets_dic

    def create_oath_session(self, oath_key_dict):
        oath = OAuth1Session(
                oath_key_dict["consumer_key"],
                oath_key_dict["consumer_secret"],
                oath_key_dict["access_token"],
                oath_key_dict["access_token_secret"]
        )
        return oath

    def tweet_search(self, search_word, oath_key_dict):
        searchtweets = SearchTweets()
        url = "https://api.twitter.com/1.1/search/tweets.json?"
        params = {
            "q": unicode(search_word),
            "lang": "ja",
            "result_type": "recent",
            "count": "100"
            }
        oath = searchtweets.create_oath_session(oath_key_dict)
        responce = oath.get(url, params = params)
        if responce.status_code != 200:
            print "Error code: %d" %(responce.status_code)
            return None
        tweets = json.loads(responce.text)
        return tweets
