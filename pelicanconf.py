#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = u'Nathan Williams'
SITENAME = u'Brownian Motion'
SITEURL = 'https://nathanwilliams.github.io'
GITHUB_URL = 'https://github.com/NathanWilliams/'

TIMEZONE = 'Australia/Sydney'

DEFAULT_LANG = u'en'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True

DEFAULT_PAGINATION = 10

ARTICLE_URL = '{date:%Y}/{date:%m}/{date:%d}/{slug}/'
ARTICLE_SAVE_AS = '{date:%Y}/{date:%m}/{date:%d}/{slug}/index.html'
THEME='foundation-default-colours'
PLUGIN_PATHS = []
PLUGINS = []

GOOGLE_ANALYTICS='UA-38967315-1'

LINKS=[("GitHUb repo","https://github.com/NathanWilliams/")]

MONTH_ARCHIVE_SAVE_AS='{date:%Y}/{date:%m}/index.html'
YEAR_ARCHIVE_SAVE_AS = '{date:%Y}/index.html'

STATIC_PATHS = ['images']
