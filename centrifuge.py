#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  fetch_timeline.py
#  centrifuge
#

import os
import sys
import cmd
import re
import HTMLParser
import textwrap
import webbrowser
import logging

from clint.textui import colored
#import pymongo

import twitter
from twitter.cmdline import CONSUMER_KEY, CONSUMER_SECRET

DB_NAME = 'centrifuge'
OAUTH_FILE = '~/.twitter_oauth'
WIDTH_TOLERANCE = 2
LOG_FILE = None


if LOG_FILE:
    logging.basicConfig(filename=os.path.expanduser(LOG_FILE),
            level=logging.DEBUG)


class TwitterCursor(object):
    """
    Provide stateful iteration up and down the timeline, anchored around the
    initial set of tweets pulled.
    """
    def __init__(self):
        logging.info('Connecting to twitter')
        self.tw = self.connect()
        self.above = []
        logging.info('Asking for 20 tweets')
        self.below = list(reversed(self.tw.statuses.home_timeline(count=20)))
        logging.info('Got %d' % len(self.below))
        self.oldest_seen = sys.maxint
        self.newest_seen = None

    def connect(self):
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

    def iterolder(self):
        while True:
            while self.below:
                t = self.below.pop()
                self.oldest_seen = min(self.oldest_seen, t['id'])
                self.newest_seen = max(self.newest_seen, t['id'])
                yield t

            self.below = list(reversed(self.tw.statuses.home_timeline(
                    count=20, max_id=self.oldest_seen - 1)))

    def pushback_older(self, t):
        self.below.append(t)

    def iternewer(self):
        newest = self.above[0]['id'] if self.above else self.newest_seen
        self.above[0:0] = list(reversed(self.tw.statuses.home_timeline(
                count=20, since_id=newest)))
        while self.above:
            t = self.above.pop()
            self.oldest_seen = min(self.oldest_seen, t['id'])
            self.newest_seen = max(self.newest_seen, t['id'])
            yield t


class InteractiveStream(cmd.Cmd):
    def __init__(self):
        cmd.Cmd.__init__(self)
        self.tw = TwitterCursor()
        self.current = None
        self.h = HTMLParser.HTMLParser()

    def _get_console_size(self):
        return map(int, os.popen('stty size', 'r').read().split())

    def do_s(self, line):
        "Fetch recent stream."
        os.system('clear')
        height, width = self._get_console_size()
        logging.info('Console is %dx%d' % (width, height))
        remaining = height - 1
        self.current = []

        for i, t in enumerate(self.tw.iterolder()):
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

            tweet_height = len(lines) + 1
            logging.debug('Tweet height is %d, got %d left' % (
                    tweet_height,
                    remaining,
                ))
            if tweet_height > remaining:
                # XXX push back tweet?
                logging.debug("Couldn't fit tweet -- finishing layout")
                self.tw.pushback_older(t)
                break

            lines = [l for l in self._format_lines(i, lines)]
            print '\n'.join(lines)
            print
            remaining -= tweet_height
            logging.debug("Included tweet, got %d left" % remaining)
            self.current.append(t)

        if remaining > 1:
            print '\n' * (remaining - 1)

    def do_EOF(self, l):
        return True

    def do_q(self, l):
        "Quit."
        return True

    def do_o(self, *args):
        "Open the URL in a tweet."
        try:
            args = map(int, args)
        except ValueError:
            print 'Just number the tweets with urls you want to open.\n'
            return

        print 'Opening %d urls' % len(args)
        for i in args:
            if i < 1 or i > len(self.current):
                print 'No tweet numbered %d -- skipping' % i
                continue

            urls = self.current[i - 1]['entities']['urls']
            if not urls:
                print 'No urls for tweet %d -- skipping' % i
                continue

            # XXX what about multi-url case?
            webbrowser.open_new_tab(urls[0]['url'])

    def highlight_text(self, text):
        text = re.sub(u'(@[A-Za-z0-9_]+)', str(colored.blue('\\1')), text,
                re.UNICODE)
        text = re.sub(u'(https?://[^ "\'”“]+)', str(colored.cyan('\\1')), text,
                re.UNICODE)
        text = re.sub(u'(#[^,.:; ]+)', str(colored.green('\\1')), text)
        text = re.sub(u' +', ' ', text, re.UNICODE)
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
