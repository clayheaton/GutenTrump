import tweepy
from time import sleep
from credentials import *
from topics import *

import json
import glob
import markovify
import random
import nltk
import re

# https://www.digitalocean.com/community/tutorials/how-to-create-a-twitterbot-with-python-3-and-the-tweepy-library

bot_version = "1.0"
global_state_size = 2

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

# Subclass to allow POS tagged text models.
class POSifiedText(markovify.Text):
    def word_split(self, sentence):
        words = re.split(self.word_split_pattern, sentence)
        words = [ "::".join(tag) for tag in nltk.pos_tag(words) ]
        return words

    def word_join(self, words):
        sentence = " ".join(word.split("::")[0] for word in words)
        return sentence

# Create models
# Heart of Darkness
print("Building Heart of Darkness model.")
with open("heart_of_darkness.txt") as hod:
    hodtext = hod.read().replace("\n"," ").replace("  "," ")
    
hod_model = POSifiedText(hodtext,state_size=global_state_size)

# Lusty Romance model
print("Building Lusty Romance model.")
with open("lusty_romance.txt") as lusty:
    lustytext = lusty.read().replace("\n"," ").replace("  "," ")
    
lusty_model = POSifiedText(lustytext,state_size=global_state_size)

# Trump model
print("Building Trump model.")
with open("trump.txt") as trump:
    trumptext = trump.read().replace("\n"," ").replace("  "," ")
    
trump_model = POSifiedText(trumptext,state_size=global_state_size)

# Lovecraft model
print("Building HP Lovecraft model.")
with open("lovecraft.txt") as lovecraft:
    lovecrafttext = lovecraft.read().replace("\n"," ").replace("  "," ")
    
lovecraft_model = POSifiedText(lovecrafttext,state_size=global_state_size)

print("Building combo model for tweets beginning with a certain phrase.")
model_combo = markovify.combine([trump_model,lovecraft_model,hod_model,lusty_model], [2,2,1,1])

modelsets = [
    [trump_model,lovecraft_model],
    [trump_model,hod_model],
    #[trump_model,lusty_model],
    [trump_model,lovecraft_model,hod_model],
    #[trump_model,lovecraft_model,lusty_model],
    #[trump_model,hod_model,lusty_model],
    [trump_model,lovecraft_model,hod_model,lusty_model]
]


def tweet_stream(num_tweets,keyword=None,models=[],weights=[],max_tries=500):
    tweets = []
    if len(models) == 0:
        models = [trump_model,lovecraft_model]
        
    made_weights = False
    if len(weights) == 0:
        weights = [[random.random()*4+1,random.random()*2+1] for n in range(num_tweets)]
        made_weights = True
    else:
        model_combo = markovify.combine(models, weights)

    tries = 0

    for i,idx in enumerate(range(num_tweets)):
        if made_weights:
            model_combo = markovify.combine(models, weights[idx])

        if keyword:
            found = False
            while found is False:
                s = model_combo.make_short_sentence(140)
                if s and keyword in s.replace(",","").replace(".","").replace("!","").split():
                    tweets.append(s)
                    found = True
                else:
                    tries += 1
                    if tries > max_tries:
                        keyword = None
                        print("**Max tries exceeded")
                        return tweet_stream(num_tweets,keyword,models,trump_weight,other_weight,max_tries)
        else:
            s = model_combo.make_short_sentence(140)
            tweets.append(s)
    return tweets

def tweet_stream_starts_with(tweet_start,num_tweets=3,max_length=140):
    tweets = []
    while len(tweets) < num_tweets:
        tweet = model_combo.make_sentence_with_start(tweet_start)
        if len(tweet) > max_length:
            continue
        else:
            tweets.append(tweet)
            
    return tweets

def make_modelweights(length_of_modelset):
    return [2] + [0.5+random.random()*1.5 for n in range(length_of_modelset - 1)]

def main():
    # api.update_status("GutenTrump version " + bot_version + " initialized.")
    factor = int(1 + random.random()*100)
    print("")
    print("Decision factor:",factor)
    sleep(5)

    if factor > 80:
        # random
        print("** RANDOM STREAM")
        n_tweets     = int(1 + random.random()*4)
        modelset     = random.choice(modelsets)
        modelweights = make_modelweights(len(modelset))
        tweets       = tweet_stream(n_tweets,models=modelset,weights=modelweights)

    elif factor > 50:
        # starts with
        print("** STARTS WITH STREAM")
        n_tweets = int(2 + random.random()*3)
        starter  = random.choice(starts_with_list)
        tweets   = tweet_stream_starts_with(starter,num_tweets=n_tweets)

    else:
        # topical storm
        print("** TOPICAL STREAM")
        n_tweets     = int(2 + random.random()*4)
        modelset     = random.choice(modelsets)
        modelweights = make_modelweights(len(modelset))
        topic        = random.choice(topic_list)
        print("** Generating tweets with topic:",topic)
        tweets       = tweet_stream(n_tweets,keyword=topic,models=modelset,weights=modelweights)

    for tweet in tweets:
        try:
            print(tweet)
            api.update_status(tweet)
        except tweepy.TweepError as e:
            print(e.reason)

        sleep(15)



if __name__ == '__main__':
    #main()
    while True:
        main()
        sleeptime = int(random.random()*1800 + 1800)
        print("Sleeping seconds:",sleeptime)
        sleep(sleeptime)