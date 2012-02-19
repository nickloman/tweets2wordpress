#!/usr/bin/env python
import sys
import re
import MySQLdb

dry_run = False
reverse_tweets = True

db=MySQLdb.connect(host="localhost",user="wordpress", passwd="password",db="wordpress")
db.set_character_set('utf8')
dbc = db.cursor()
dbc.execute('SET NAMES utf8;')
dbc.execute('SET CHARACTER SET utf8;')
dbc.execute('SET character_set_connection=utf8;')

date_str = "datetime('2012-02-18 09:00:00')"

try:
        import sqlite3
except Exception:
        from pysqlite2 import dbapi2 as sqlite3

def autolink(html):
    # match all the urls
    # this returns a tuple with two groups
    # if the url is part of an existing link, the second element
    # in the tuple will be "> or </a>
    # if not, the second element will be an empty string
    urlre = re.compile("(\(?https?://[-A-Za-z0-9+&@#/%?=~_()|!:,.;]*[-A-Za-z0-9+&@#/%=~_(|])(\">|</a>)?")
    urls = urlre.findall(html)
    clean_urls = []

    # remove the duplicate matches
    # and replace urls with a link
    for url in urls:
        # ignore urls that are part of a link already
        if url[1]: continue
        c_url = url[0]
        # ignore parens if they enclose the entire url
        if c_url[0] == '(' and c_url[-1] == ')':
            c_url = c_url[1:-1]

        if c_url in clean_urls: continue # We've already linked this url

        clean_urls.append(c_url)
        # substitute only where the url is not already part of a
        # link element.
        html = re.sub("(?<!(=\"|\">))" + re.escape(c_url), 
                      "<a rel=\"nofollow\" href=\"" + c_url + "\">" + c_url + "</a>",
                      html)
    return html

def format_tweet(row):
	return "<a href=\"https://twitter.com/#!/%s\">%s</a>: %s\n" % (row['author'], row['author'], autolink(row['content']))

def popular_tweets():
	popular = ''
	c = conn.cursor()
	c.execute("select count(*) n, t1.retweet_of, t2.content, t2.author from tweets t1, tweets t2 where t2.content NOT LIKE '%%notAGBT%%' AND t1.retweet_of = t2.tweet_id and t2.created_at > %s group by t1.retweet_of order by n desc limit 30" % (date_str,))
	rows = c.fetchall()
	for row in rows:
		popular += "(%s) %s" % (row['n'], format_tweet(row))
	return popular

conn = sqlite3.connect(sys.argv[1])
conn.row_factory = sqlite3.Row

popular = popular_tweets()

c = conn.cursor()
c.execute("SELECT * FROM tweets WHERE content NOT LIKE '%%notAGBT%%' AND retweeted = 0 AND created_at > %s ORDER BY DATETIME(created_at)" % (date_str,))
buff = ""

last_hour = 0

hours = []
for row in c:
	if row['retweet_count'] > 1:
		print row

	post_time = row['created_at'][11:]
	h, m, s = [int(x) for x in post_time.split(":")]

	h -= 5
	if h < 0:
		h += 24

	if h > last_hour:
		hours.append(buff)
		buff = ''
		if h >= 11:
			its = "pm"
		else:
			its = "am"
		dh = h
		dj = h + 1
		if dh > 12:
			dh -= 12
		if dj > 12:
			dj -= 12

		buff += "\n<strong>%d - %d%s EST</strong>\n" % (dh, dj, its)
		last_hour = h

	buff += "+%dm <a href=\"https://twitter.com/#!/%s\">%s</a>: %s\n" % (m, row['author'], row['author'], autolink(row['content']))

hours.append(buff)

#for b in hours[::-1]:
#	print b

dbc.execute("SELECT post_content FROM wp_posts WHERE ID = %d" % int(sys.argv[2]))

newbuf = ''
content = dbc.fetchone()[0]

pos = content.find('<REPLACE></REPLACE>')
newbuf += content[0:pos]
newbuf += "<REPLACE></REPLACE>\n"
newbuf += "<strong>Most popular tweets</strong>\n"
newbuf += popular.encode('ascii', 'ignore')

if reverse_tweets:
	hours = hours[::-1]

for b in hours:
	newbuf += b.encode('ascii', 'ignore')
print newbuf

if not dry_run:
	dbc.execute("UPDATE wp_posts SET post_content = %s WHERE ID = %s",
 		(newbuf, int(sys.argv[2])))
