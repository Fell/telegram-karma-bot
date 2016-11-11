# -*- coding: utf-8 -*-

import sys
import time
import random
import datetime, time
import telepot
import redis
import operator
from operator import itemgetter

BOT_TOKEN =  '123456789:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

help_msg = """
/+ str - increase karma for "str"
/- str - decrease karma for "str"
/rank str - get rankings for "str"
/roll - roll a dice
/help - get help

All other commands will be ignored.

My source code: https://github.com/br0ziliy/telegram-karma-bot
"""

try:
    r = redis.StrictRedis(host='localhost', port=6379, db=0)
except ConnectionError:
    print "Redis connection failed"
    raise SystemExit(1)

def handle_vote(msg,direction):
    duser = msg['text'].split()[1]
    suser = msg['from']['id']

    sname = ''
    if 'username' in msg['from']: sname = msg['from']['username']

    if duser.startswith('@'): duser = duser[1:]

    duser = duser.lower()
    sname = sname.lower()

    now = time.time()
    last = r.hget(duser, suser)
    delta = 31337
    if last: delta = now - float(last)

    print u"Handling karma {} from {} to {} (last handled: {} seconds ago)".format(direction, sname.encode('utf8'), duser, delta)
    if duser == sname:
        return u"@{} public masturbation is not allowed.".format(sname)
    if delta < 120:
        return u"@{} cooldown: {} seconds left".format(sname, 120 - int(delta))
    r.hset(duser,suser,time.time())
    if direction == 'up':
        r.hincrby(duser,'0karma_',1)
    elif direction == 'down':
        r.hincrby(duser,'0karma_',-1)
    return u"@{}'s karma is now *{}*".format(duser, r.hget(duser,'0karma_'))

def handle_top():
    result = ''
    list = {}

    keys = r.keys('*')

    for key in keys:
        if r.type(key) == 'hash': 
            list[key] = r.hget(key, '0karma_')

    list = sorted(list.items(), key=itemgetter(1), reverse=True)

    counter = 1
    for (user, karma) in list:
        result += "{}. @{}: *{}*\r\n".format(counter, user, karma)
        counter += 1
        if(counter > 10): break

    return 'Karma Top 10:\r\n{}'.format(result)

def handle_karma(duser):

    if duser.startswith('@'): duser = duser[1:]
    duser = duser.lower()

    return u"@{} has *{}* karma.".format(duser, r.hget(duser,'0karma_'))

def handle(msg):
    chat_id = msg['chat']['id']
    chat_type = msg['chat']['type']
    try:
        from_name = msg['from']['username']
    except KeyError:
        from_name = "UNKNOWN_USER"
    try:
        command = msg['text'].split()[0]
    except KeyError: # not a text message?
        print u"Not text message - ignoring: %s" % msg
        return
    param = None
    try:
        param = msg['text'].split()[1]
        param = param.encode('utf8')
    except IndexError:
        print "Command with no parameter"
        param = None
    command = command.split('@')[0]
    print "Got command: {} {} from: {}".format(command,param,from_name)

    if command == '/roll':
        if param: bot.sendMessage(chat_id, '@{} rolls {}'.format(from_name, random.randint(1,int(param))))
        else: bot.sendMessage(chat_id, '@{} rolls {}'.format(from_name, random.randint(1,100)))
    elif command == '/top':
        bot.sendMessage(chat_id, handle_top(), parse_mode='Markdown')
    elif command == '/karma' or command == '/rank':
        if param: bot.sendMessage(chat_id, handle_karma(param), parse_mode='Markdown')
        else: bot.sendMessage(chat_id, 'Usage: {} username'.format(command))
    elif command == '/+' or command == '/plus':
        if param: bot.sendMessage(chat_id, handle_vote(msg, 'up'), parse_mode='Markdown')
        else: bot.sendMessage(chat_id, 'Usage: {} username'.format(command))
    elif command == '/-' or command == '/minus':
        if param: bot.sendMessage(chat_id, handle_vote(msg, 'down'), parse_mode='Markdown')
        else: bot.sendMessage(chat_id, 'Usage: {} username'.format(command))
    elif command == '/help':
        if chat_type == "private":
            bot.sendMessage(chat_id, help_msg, disable_web_page_preview=True)
        else:
            bot.sendMessage(chat_id, "Talk to me privately for help.")

bot = telepot.Bot(BOT_TOKEN)
bot.message_loop(handle)
print 'I am listening ...'

while 1:
    time.sleep(10)
