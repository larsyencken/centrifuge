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
WIDTH_TOLERANCE = 2


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

    def _get_console_size(self):
        return map(int, os.popen('stty size', 'r').read().split())

    def do_s(self, line):
        "Fetch recent stream."
        os.system('clear')
        tweets = self.tw.statuses.home_timeline()[:10]
        height, width = self._get_console_size()
        remaining = height - 1

        for i, t in enumerate(tweets):
            user = t['user']['screen_name']
            name = t['user']['name'].strip()
            text = t['text']
            m = re.match('^RT (@[a-zA-Z0-9_]+): ', text)
            if m:
                author = u'%s, via %s (%s)' % (
                        colored.red(m.group(1)),
                        colored.red('@%s' % user),
                        name
                    )
                text = text.split(': ', 1)[1]
            else:
                author = u'%s (%s)' % (colored.red('@%s' % user), name)

            indent = 4
            lines = map(self.highlight_text, textwrap.wrap(
                    self.h.unescape(text),
                    width - indent - WIDTH_TOLERANCE
                ))
            lines.append(author)

            tweet_height = len(lines) + 2
            if tweet_height > remaining:
                break

            lines = [l for l in self._format_lines(i, lines)]
            print '\n'.join(lines)
            print
            remaining -= tweet_height

        print '\n' * (remaining - 1)

        self.current = tweets[:i + 1]

    def do_EOF(self, l):
        return True

    def do_q(self, l):
        "Quit."
        return True

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

    def _format_lines(self, i, lines):
        r = []
        r.append(u'%2d. %s' % (i + 1, lines[0]))
        for l in lines[1:]:
            r.append(u'    %s' % l)
        return r


def main():
    try:
        stream = InteractiveStream()
        stream.cmdloop()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
