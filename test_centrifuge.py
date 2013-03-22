#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  test_centrifuge.py
#  centrifuge
#

import itertools
import unittest

import centrifuge


class MockTwitterApi(object):
    @property
    def statuses(self):
        return self

    def home_timeline(self, count=5, since_id=None, max_id=None):
        ts = []
        anchor_id = max_id or 50000
        for i in xrange(count):
            ts.append({
                    'id': anchor_id - i,
                    'text': 'Blah blah blah #yeah',
                })
        return ts


class TwitterCursorTest(unittest.TestCase):
    def setUp(self):
        self.c = centrifuge.TwitterCursor(api=MockTwitterApi())

    def test_getting_older_tweets(self):
        t = self.c.iterolder().next()
        t2 = self.c.iterolder().next()

        assert t['id'] > t2['id']

    def test_paginating_older_tweets(self):
        ts = list(itertools.islice(self.c.iterolder(), 100))
        assert sorted(ts, key=lambda t: t['id'], reverse=True) == ts
        self.assertEqual(len(ts), len(set(t['id'] for t in ts)))


def suite():
    return unittest.TestSuite((
            unittest.makeSuite(),
        ))


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=1).run(suite())
