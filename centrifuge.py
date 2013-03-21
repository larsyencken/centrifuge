#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  fetch_timeline.py
#  centrifuge
#

import os
import cmd
import re
import HTMLParser
import textwrap
#import webbrowser

from clint.textui import colored
import pymongo

import twitter
from twitter.cmdline import CONSUMER_KEY, CONSUMER_SECRET

DB_NAME = 'centrifuge'
OAUTH_FILE = '~/.twitter_oauth'


def twitter_connect():
    oauth_token, oauth_secret = twitter.read_token_file(
            os.path.expanduser(OAUTH_FILE)
        )

    t = twitter.Twitter(auth=twitter.OAuth(
            oauth_token,
            oauth_secret,
            CONSUMER_KEY,
            CONSUMER_SECRET,
        ))

    return t


class InteractiveStream(cmd.Cmd):
    def __init__(self):
        cmd.Cmd.__init__(self)
        self.tw = twitter_connect()
        self.db = getattr(pymongo.Connection(), DB_NAME)
        self.current = []
        self.h = HTMLParser.HTMLParser()

    def _get_width(self):
        return map(int, os.popen('stty size', 'r').read().split())[1]

    def do_s(self, line):
        "Fetch recent stream."
        tweets = self.tw.statuses.home_timeline()[:10]
        width = self._get_width()
        self.current = tweets
        for i, t in enumerate(tweets):
            user = t['user']['screen_name']
            name = t['user']['name'].strip()
            lines = map(self.highlight_text, textwrap.wrap(
                    self.h.unescape(t['text']),
                    width - 6
                ))
            print u'%2d. %s' % (i + 1, lines[0])
            for l in lines[1:]:
                print u'    %s' % l
            print '   ', colored.red('@%s' % user), '(%s)' % name
            print

    def do_EOF(self, l):
        return True

    def do_q(self, l):
        "Quit."
        return True

    def do_c(self, l):
        "Clear the screen."
        os.system('clear')

    def do_o(self, i, j=None):
        "Open the URL in a tweet."
        pass

    def highlight_text(self, text):
        text = re.sub('(@[A-Za-z0-9_]+)', str(colored.blue('\\1')), text,
                re.UNICODE)
        text = re.sub('(https?://[^ ]+)', str(colored.cyan('\\1')), text,
                re.UNICODE)
        text = re.sub('(#[^,.:; ]+)', str(colored.green('\\1')), text)
        text = re.sub(' +', ' ', text, re.UNICODE)
        return text


def main():
    try:
        stream = InteractiveStream()
        stream.cmdloop()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
