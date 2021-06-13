import mysql.connector
from mysql.connector import Error
import os
import json
import praw
import time
import tweepy
from datetime import datetime
from pytz import timezone
from unidecode import unidecode
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from config import consumer_key, consumer_secret, access_token, access_token_secret, password


analyzer = SentimentIntensityAnalyzer()

track = ['Tsla']
consumer_key = config.consumer_key
consumer_secret = config.consumer_secret
access_token = config.access_token
access_token_secret = config.access_token_secret
password = config.password

# consumer_key = os.environ['CONSUMER_KEY']
# consumer_secret = os.environ['CONSUMER_SECRET']
# access_token = os.environ['ACCESS_TOKEN']
# access_token_secret = os.environ['ACCESS_TOKEN_SECRET']
# password = os.environ['PASSWORD']

def datetime_from_utc_to_local(utc_datetime):
    now_timestamp = time.time()
    offset = datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(now_timestamp)
    return utc_datetime + offset

def connect(timestamp_ms, sentiment):
	"""
	connect to MySQL database and insert twitter data
	"""
	try:
		con = mysql.connector.connect(
		host = 'localhost',
		database='twitterdb', 
		user='root', 
		password = password)
		print("You are connected to mySQL")
		

		if con.is_connected():
			"""
			Insert twitter data
			"""
			cursor = con.cursor()
			# twitter
			query = "INSERT INTO TwitterSent (timestamp_ms, sentiment) VALUES (%s, %s)"
			cursor.execute(query, (timestamp_ms, sentiment))
			con.commit()
			
			
	except Error as e:
	
		print(e)

	cursor.close()
	con.close()

	return


# Tweepy class to access Twitter API
class Streamlistener(tweepy.StreamListener):
	

	def on_connect(self):
		print("You are connected to the Twitter API")


	def on_error(self):
		if status_code != 200:
			print("error found")
			# returning false disconnects the stream
			return False

	"""
	This method reads in tweet data as Json
	and extracts the data we want.
	"""
	def on_data(self,data):
		
		try:
			data = json.loads(data)

			if 'truncated' not in data:
				return True
			if data['truncated']:
				tweet = unidecode(data['extended_tweet']['full_text'])
			else:
				tweet = unidecode(data['text'])

			#Takes in string stream data and converts it into a different format
			timestamp_ms = datetime.strftime(datetime.strptime(data['created_at'], '%a %b %d %H:%M:%S +0000 %Y'), '%Y-%m-%d %H:%M:%S')
			#converts it back into a datetime object to pass it through datetime_from_utc_to_local
			timestamp_ms = datetime.strptime(timestamp_ms, '%Y-%m-%d %H:%M:%S')
			#run it through the created method
			timestamp_ms = datetime_from_utc_to_local(timestamp_ms)


			tweet = data['text']
			vs = analyzer.polarity_scores(tweet)
			sentiment = vs['compound']
			#insert data just collected into MySQL database
			connect(timestamp_ms, sentiment)
			print("Tweet collected at: {} ".format(str(timestamp_ms)))
		except Error as e:
			print(e)


if __name__== '__main__':

	# authentification so we can access twitter
	auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
	auth.set_access_token(access_token, access_token_secret)
	api =tweepy.API(auth, wait_on_rate_limit=True)

	# create instance of Streamlistener
	listener = Streamlistener(api = api)
	stream = tweepy.Stream(auth, listener = listener)

	#track = ['nba', 'cavs', 'celtics', 'basketball']
	# choose what we want to filter by
	stream.filter(track = track, languages = ['en'])