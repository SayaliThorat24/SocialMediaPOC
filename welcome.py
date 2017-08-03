# Copyright 2015 IBM Corp. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from flask import Flask, jsonify, render_template, request, redirect
import tweepy
import keys
#from tweetClass import Tweet
from watson_developer_cloud import ToneAnalyzerV3
from operator import itemgetter
from watson_developer_cloud import ConversationV1

import os
proxy = 'https://proxy.keybank.com:80'
os.environ['http_proxy'] = proxy 
os.environ['https_proxy'] = proxy
os.environ['HTTP_PROXY'] = proxy
os.environ['HTTPS_PROXY'] = proxy

app = Flask(__name__)
auth = tweepy.OAuthHandler(keys.consumer_key, keys.consumer_secret)
auth.set_access_token(keys.access_token, keys.access_token_secret)
api = tweepy.API(auth)

@app.route('/')
def Welcome():
    return app.send_static_file('index.html')

@app.route("/<name>",  methods = ['GET', 'POST']) 
def CollectTweets(name=None):   
    tone_analyzer = ToneAnalyzerV3(
            username='228d1995-d986-4766-84aa-387e0d0978ef',
            password='mIjxH6u1o8sK',
            version='2016-02-11')
    
    conversation = ConversationV1(
            username='44155676-ae90-45d0-b2af-d95b4ba0cba8',
            password='dXCx47VBwLPw',
            version='2017-05-26')
    
    toneCategoryArray = []
    tones = []
    public_tweets = api.mentions_timeline()
    flag = 0
    tweets = []
    workspace_id = '14d740b5-4397-4860-bec9-38aaf91f4f7b'
    
    for tweet in public_tweets:
        tw = []
        tweeturl = 'https://twitter.com/'+tweet.user.screen_name+'/status/'+str(tweet.id)
        text = tweet.text
        output=tone_analyzer.tone(text)
        toneCatLength = len(output['document_tone']['tone_categories'])
        i = 0
        tonesArray =  []
        
        #Add tweet details
        tw.append(tweet.user.screen_name)
        tw.append(text)
        tw.append(tweeturl)
        tw.append(tweet.id)
        
        #Tone sentiment analysis
        while i<toneCatLength:
            tonesLength = len(output['document_tone']['tone_categories'][i]['tones'])
            j=0
            while j<tonesLength:
                score = output['document_tone']['tone_categories'][i]['tones'][j]['score']
                scores = (score*100)
                tonesArray.append(str(scores))
                tw.append(scores)
                if flag == 0:
                    name = output['document_tone']['tone_categories'][i]['tones'][j]['tone_name']
                    tones.append(name)
                j+=1
            i+=1
        toneCategoryArray.append(tonesArray)
        
        #Generate Response message
        context = {}
        response = conversation.message(
                workspace_id=workspace_id,
                message_input={'text': text},
                context=context)
        tw.append(response['output']['text'][0])
        tweets.append(tw)
        flag+=1
    
    #Sort tweets based on Anger sentiment
    tweets = sorted(tweets, key=itemgetter(4), reverse=True)
    
    #return render_template('index.html')
    return render_template('tweets_v2.html', tweets=tweets, tones=tones, tweetLen=len(public_tweets), toneLen=len(tones)+4)
    #return render_template('tweets_v2_1.html', tweets=tweets, tones=tones, tweetLen=len(public_tweets), toneLen=len(tones)+4)

@app.route("/posttweet/", methods=['POST'])
def TweetResponse():
    msg= request.form['msg']
    tweetId = request.form['id']
    username = request.form['username']
    name = request.form['name']
    
    #Repond to the tweet
    replyText = '@' + username + ' ' + msg
    api.update_status(status=replyText, in_reply_to_status_id=tweetId)
    
    #redirect to the hello page
    url='/'+name
    return redirect(url)          

@app.route('/api/people/<name>')
def SayHello(name):
    message = {
        'message': 'Hello ' + name
    }
    return jsonify(results=message)

port = os.getenv('PORT', '4000')
if __name__ == "__main__":
	app.run(host='127.0.0.1', port=int(port))
