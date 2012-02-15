# Requirs: tweepy http://code.google.com/p/tweepy/

tweet_table = """
CREATE TABLE tweets (
    id INTEGER PRIMARY KEY,
    tweet_id VARCHAR(40),
    author VARCHAR(40),
    content VARCHAR(140),
    in_reply_to_screen_name VARCHAR(40),
    in_reply_to_status_id VARCHAR(40),
    in_reply_to_status_id_str VARCHAR(40),
    in_reply_to_user_id VARCHAR(40),
    in_reply_to_user_id_str VARCHAR(40),
    retweet_count INTEGER,
    retweeted INTEGER,
    created_at TEXT
)
"""

import tweepy
from tweepy.streaming import StreamListener, Stream
import authkeys
import sqlite3
import sys
import os.path

CONSUMER_KEY = '9seZZJaHlKzdrzfXAcXpQ'
CONSUMER_SECRET = 'FQbkrYXeTjA1M5JBolXkK1nKIKd7ap0nEN5Dgt5MBTs'

try:
    import authkeys
except Exception:
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth_url = auth.get_authorization_url()
    print 'Please authorize: ' + auth_url
    verifier = raw_input('PIN: ').strip()
    auth.get_access_token(verifier)
    fh = open("authkeys.py", "w")
    print >>fh, "ACCESS_KEY = '%s'" % auth.access_token.key
    print >>fh, "ACCESS_SECRET = '%s'" % auth.access_token.secret
    fh.close()
    import authkeys

ACCESS_KEY = authkeys.ACCESS_KEY
ACCESS_SECRET = authkeys.ACCESS_SECRET

makedb = False
if not os.path.exists(sys.argv[1]):
    makedb = True

conn = sqlite3.connect(sys.argv[1])
if makedb:
    c = conn.cursor()
    c.execute(tweet_table)
    conn.commit()

class Listener ( StreamListener ):
    def on_status( self, status ):
        print '-' * 20
        print status.text.encode('ascii', 'ignore')

        c = conn.cursor()

        insert_data = (
            status.id_str,
            status.author.screen_name,
            status.text,
            status.in_reply_to_screen_name,
            status.in_reply_to_status_id,
            status.in_reply_to_status_id_str,
            status.in_reply_to_user_id,
            status.in_reply_to_user_id_str,
            status.retweet_count,
            "%d" % (status.retweeted,),
            status.created_at
        )

        c.execute("""
        INSERT INTO tweets ( id, tweet_id, author, content, in_reply_to_screen_name,
                             in_reply_to_status_id, in_reply_to_status_id_str,
                             in_reply_to_user_id, in_reply_to_user_id_str,
                             retweet_count, retweeted, created_at )
        VALUES ( NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? )""", insert_data)
        conn.commit()
        return

    def on_error( self, error ):
        print error
        return

#auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
#auth_url = auth.get_authorization_url()
#print 'Please authorize: ' + auth_url
#verifier = raw_input('PIN: ').strip()
#auth.get_access_token(verifier)
#print "ACCESS_KEY = '%s'" % auth.access_token.key
#print "ACCESS_SECRET = '%s'" % auth.access_token.secret
#raise SystemExit

if __name__ == "__main__":
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)

    listener = Listener()
    stream = Stream(auth, listener);
    stream.filter(track=[sys.argv[2]])
