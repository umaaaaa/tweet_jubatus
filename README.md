#辰巳PA検問に関するツイートのクラスタリング

##はじめに
辰巳PAでの検問情報がTwitter上に流れてきます。これらの情報を形態素解析と機械学習にかけてクラスタリングしてみたいと思います。

###使用するもの
* Ubuntu 14.04
* Jubatus
* MongoDB
* MeCab

##準備
###Jubatus
はじめに、Jubatusを使用できるようにします。以下のコマンドを実行しましょう。ついでにオプションのmecab関連もインストールしましょう

```
$ deb http://download.jubat.us/apt binary/
$ sudo apt-get
$ sudo apt-get install jubatus mecab-jumandic-utf8
```
これでJubatusが使える環境になりました。Jubatusを使用するには以下のコマンドを実行し、環境変数を読み込んでください。Vagrant等の仮想環境で動かしている場合は、Vagrantを立ち上げる度に以下を実行して、環境変数を読み込んでください。

```
$ source /opt/jubatus/profile
```
今回は、Pythonを使用するので、pipを使ってJubatusモジュールをインストールしましょう。あとは今回必要なモジュールもまとめてインストールしてしまいましょう

```
$ pip install -r requirements.txt
```

###MongoDB
次に、MongoDBをインストールしていきましょう。デフォルトのapt-getには存在しないので、リポジトリを追加します。そして、MongoDBを起動しましょう。

```
$ sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 7F0CEB10
$ echo 'deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen' | sudo tee /etc/apt/sources.list.d/mongodb.list
$ sudo apt-get update
$ sudo apt-get install mongod-10gen
$ sudo service mongod start
```

次に、MongoDBに``tweetdb``というDBを構築してみましょう。

```
$ mongo
MongoDB shell version: 2.4.14
connecting to: test
> use tweetdb
switched to db tweetdb
```
最後に、MongoDBのIPアドレスを``ifconfig``で確認しておきましょう。  
MongoDBの設定は以上です。

###MeCab
形態素解析を行うためのMeCabをインストールしましょう。

```
$ sudo apt-get install mecab libmecab-dev mecab-ipadic
$ sudo aptitude install mecab-ipadic-utf8
$ sudo apt-get install python-mecab
```

##Twitterの検索ワード取得
辰巳PAの検問情報は``無料車検``という隠語で表現されたりします。なので今回は、``辰巳 車検``というワードを抽出したいと思います。抽出したワードはMongoDBの``tweets``という名前のコレクションに保存します。

###教師データの作成
Jubatusのクラスタリング(Classifier)には、教師データが必要となります。教師データを蓄積していくにはそれなりに日数が必要です。定期的に教師データを更新できるようなプログラムを書きます。  
``辰巳 車検``でヒットしたツイートを一つずつ表示し、現在検問が行われているツイートならば``t``を、そうでないならそれ以外を入力し、教師データを作成します。ちなみに、現在検問が行われているツイートは``true_collection``に、そうでないツイートは``false_collection``に入れられます。

```true_or_false.py
#!/usr/bin/env python
# -*- coding:utf-8 -*-

from requests_oauthlib import OAuth1Session
import json
import time, calendar
import datetime
import locale
from pymongo import MongoClient

### Constants

oath_key_dict = {
    "consumer_key": "XXXXXXXXXXXXXXXXX",
    "consumer_secret": "XXXXXXXXXXXXXXXXXXXXXX",
    "access_token": "XXXXXXXXXXXXXXXXXXXXXXX",
    "access_token_secret": "XXXXXXXXXXXXXXXXXXX"
}

# MongoDBのIP
con = MongoClient('XXX.XXX.XXX.XXX', 27017)
db = con.tweetdb
true_collection = db.true_collection
false_collection = db.fase_collection

### Functions

def YmdHMS(created_at):
    st  = time.strptime(created_at, '%a %b %d %H:%M:%S +0000 %Y')
    dt = datetime.datetime(st.tm_year,st.tm_mon,st.tm_mday,st.tm_hour,st.tm_min,st.tm_sec)
    dst = datetime.datetime.strptime(created_at,'%a %b %d %H:%M:%S +0000 %Y')
#世界標準時から日本時間にする
    japan_dst = dst + datetime.timedelta(hours=9)
    return japan_dst

def get_tweet():
    now = datetime.datetime.now()
    now_minus_six = now - datetime.timedelta(hours=6)
    # tweets = tweet_search(u"取り締まり && 299", oath_key_dict)
    tweets = tweet_search(u"車検 && 辰巳 exclude:retweets exclude:mentions", oath_key_dict)
    count = 0
    tweet_list = {}

    for tweet in tweets["statuses"]:
        Created_at = YmdHMS(tweet["created_at"])
        tweet_id = tweet[u'id_str']
        text = tweet[u'text']
        created_at = tweet[u'created_at']
        user_id = tweet[u'user'][u'id_str']
        user_description = tweet[u'user'][u'description']
        screen_name = tweet[u'user'][u'screen_name']

        tweet_list[count] = text
        count += 1

    return tweet_list

def create_oath_session(oath_key_dict):
    oath = OAuth1Session(
    oath_key_dict["consumer_key"],
    oath_key_dict["consumer_secret"],
    oath_key_dict["access_token"],
    oath_key_dict["access_token_secret"]
    )
    return oath

def tweet_search(search_word, oath_key_dict):
    url = "https://api.twitter.com/1.1/search/tweets.json?"
    params = {
        "q": unicode(search_word),
        "lang": "ja",
        "result_type": "recent",
        "count": "100"
        }
    oath = create_oath_session(oath_key_dict)
    responce = oath.get(url, params = params)
    if responce.status_code != 200:
        print "Error code: %d" %(responce.status_code)
        return None
    tweets = json.loads(responce.text)
    return tweets

def trueOrFalse(tweet_list):
    for tweet in tweet_list:
        print tweet_list[tweet]
        user_input = raw_input()
        if user_input == 't':
            true_collection.insert({'tweet':tweet_list[tweet]})
        else:
            false_collection.insert({'tweet':tweet_list[tweet]})

if __name__ == '__main__':
    tweet_list = get_tweet()
    trueOrFalse(tweet_list)
```


###MongoDB内のコレクション内データの取得
後々に、Jubatusを利用する際に、先ほど入れたデータをMongoDBから取り出す必要があります。そのためにます、``pymongo``が必要となりますので、インストールしておきましょう

```
$ sudo easy_install pymongo
```
それでは、pymongoを用いてMongoDB内の値を取得するプログラムを作成しておきましょう。

```getmongo.py
#usr/bin/env python
# -*- coding:utf-8 -*-

from pymongo import MongoClient
import json

class convertMongo:
    global true_col
    global false_col
    global col
    # mongodbのIP
    con = MongoClient('XXX.XXX.XXX.XXX', 27017)
    db = con['tweetdb']
    col = db.tweets
    true_col = db.true_collection
    false_col = db.false_collection
    global dic
    dic = {}

    def getDic(self):
        count = 0
        for data in col.find():
            del data['_id']
        # BsonB$rJsonB$KJQ49
            json_list = json.dumps(data)
        # JsonB$r%G%#%/%7%g%J%j$KJQ49
            dic[count] = json.loads(json_list)
            count += 1
        return dic

    def getTrueDic(self):
        count = 0
        for data in true_col.find():
            del data['_id']
        # BsonB$rJsonB$KJQ49
            json_list = json.dumps(data)
        # JsonB$r%G%#%/%7%g%J%j$KJQ49
            dic[count] = json.loads(json_list)
            count += 1
        return dic

    def getFalseDic(self):
        count = 0
        for data in false_col.find():
            del data['_id']
        # BsonB$rJsonB$KJQ49
            json_list = json.dumps(data)
        # JsonB$r%G%#%/%7%g%J%j$KJQ49
            dic[count] = json.loads(json_list)
            count += 1
        return dic
```

##Jubatusの利用
###Jubatusの起動
ツイート内容をMeCabを用いて形態素解析をかけ、機械学習を行います。Jubatusの設定ファイルを作成します。

```config.json
{
  "method": "NHERD",
  "parameter": {
    "regularization_weight": 0.001
  },
  "converter": {
    "num_filter_types": {
    },
    "num_filter_rules": [
    ],
    "string_filter_types": {
    },
    "string_filter_rules": [
    ],
    "num_types": {
    },
    "num_rules": [
    ],
    "string_types": {
        "bigram":  { "method": "ngram", "char_num": "2" },
        "mecab": {
          "method": "dynamic",
          "path": "libmecab_splitter.so",
          "function": "create"
        }
    },
    "string_rules": [
        { "key": "*", "type": "mecab", "sample_weight": "bin", "global_weight": "idf" }
    ]
  }
}
```
それでは、jubaclassifierを起動してみましょう。

```
$ jubaclassifier -f config.json -t 0
2015-06-16 07:34:26,214 32468 INFO  [server_util.cpp:371] starting jubaclassifier 0.7.2 RPC server at 10.0.2.15:9199
    pid                  : 32468
    user                 : vagrant
    mode                 : standalone mode
    timeout              : 0
    thread               : 2
    datadir              : /tmp
    logdir               :
    log config           :
    zookeeper            :
    name                 :
    interval sec         : 16
    interval count       : 512
    zookeeper timeout    : 10
    interconnect timeout : 10

2015-06-16 07:34:26,218 32468 INFO  [server_util.cpp:128] load config from local file: /home/vagrant/twitter/config.json
2015-06-16 07:34:26,229 32468 INFO  [dynamic_loader.cpp:87] plugin loaded: /opt/jubatus/lib/jubatus/plugin/libmecab_splitter.so.0.7.2 version: 0.7.2
2015-06-16 07:34:26,233 32468 INFO  [classifier_serv.cpp:113] config loaded: {
  "method": "NHERD",
  "parameter": {
    "regularization_weight": 0.001
  },
  "converter": {
    "num_filter_types": {
    },
    "num_filter_rules": [
    ],
    "string_filter_types": {
    },
    "string_filter_rules": [
    ],
    "num_types": {
    },
    "num_rules": [
    ],
    "string_types": {
        "bigram":  { "method": "ngram", "char_num": "2" },
        "mecab": {
          "method": "dynamic",
          "path": "libmecab_splitter.so",
          "function": "create"
        }
    },
    "string_rules": [
        { "key": "*", "type": "mecab", "sample_weight": "bin", "global_weight": "idf" }
    ]
  }
}

2015-06-16 07:34:26,236 32468 INFO  [server_helper.hpp:223] start listening at port 9199
2015-06-16 07:34:26,236 32468 INFO  [server_helper.hpp:230] jubaclassifier RPC server startup
```

###Jubatusに教師データを食わせる
それではさっそくJubatusに教師データを食わせてみましょう

```train.py
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
from getmongo import convertMongo


getmongo = convertMongo()

def train(client):
    # prepare training data
    # predict the last ones (that are commented out)
    true_dic = getmongo.getTrueDic()
    false_dic = getmongo.getFalseDic()
    train_data = []

    for line in true_dic:
        tweet = true_dic[line]['tweet']
        train_data.append(('true', Datum({'tweet':tweet})))
    for line in false_dic:
        tweet = false_dic[line]['tweet']
        train_data.append(('false', Datum({'tweet':tweet})))

    # training data must be shuffled on online learning!
    random.shuffle(train_data)

    # run train
    client.train(train_data)

if __name__ == '__main__':
    # connect to the jubatus
    client = jubatus.Classifier(host, port, name)
    train(client)
```
そして実行をします。何も出なければ成功しています。

```
$ python train.py
```

###クラスタリングする
それでは、実際にクラスタリングを行ってみましょう。

```tweet_classifier.py
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
from getmongo import convertMongo


getmongo = convertMongo()

def predict(client):
    dic = getmongo.getDic()
    data = []
    value = 0

    for line in dic:
        tweet = dic[line]['tweet']
        data.append((Datum({'tweet': tweet})))

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
```

実行してみます。

```
$ python tweet_classifier.py
true 精度は置いておいて、「辰巳 車検」のツイートを機械学習にかけてクラスタリングできた
false 辰巳で無料車検（テスト）
true YouTubeで「首都高 取り締まり GWの臨時車検に捕まる！」を見ませんか 首都高 取り締まり GWの臨時車検に捕まる！: https://t.co/PQEy9nea8D　あんときの辰巳の無料車検てこんなんやってたんだー。おっかねー(^o^;
false 辰巳で無料車検（テスト）
false 辰巳箱崎閉鎖
C1内回り無料車検(？)
true もう帰ってきた・・・
辰巳にバンの察きたからまた無料車検でもするのかって思って逃げたww
捕まるもんですか！ww
true 昨日辰巳で無料車検あったのね
false 辰巳に無料車検開店のお知らせwww
true 辰巳PAが車検場になってるか知りたい
true 先週の土曜日は辰巳無料車検やってたからなぁ（´・ω・｀）今週は大丈夫かな
```

正直精度がとても悪い。原因として、まだ15件ほどしか教師データとして渡していないことにあると思います。これから教師データを増やしていき、精度が上がることを期待します。  
