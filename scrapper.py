#!/usr/bin/env python3

import TwitterAPI
import yaml
from TwitterAPI import TwitterAPI
import argparse
import logging
import os
import json
import sys
import pprint
import datetime

logging.basicConfig(
        format='%(levelname)s %(asctime)s: %(message)s',
        level=logging.INFO
    )
log = logging.getLogger(__name__)



# keywords
# retweets
# save method: db, json
# mode: stream, search
# quota


def read_credentials(path='creds.yml'):
    with open(path) as f:
        return yaml.load(f)


ENDPOINTS = {
    'stream': 'statuses/filter',
    'search': 'search/tweets'
}

KW_QS = {
    'stream': 'track',
    'search': 'q'
}


def get_tweets(mode, keywords):
    r = api.request(ENDPOINTS[mode], {KW_QS[mode]: keywords})
    for item in r:
        yield item['text'] if 'text' in item else item

def get_quota(api):
    r = api.request('application/rate_limit_status').json()
    search_quota = r['resources']['search']['/search/tweets']
    search_quota['reset'] = datetime.datetime.fromtimestamp(
            search_quota['reset']
        ).strftime('%Y-%m-%d %H:%M:%S')
    # TODO: stream
    return {'search_quota':search_quota}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--keywords', '-k', nargs='+', help='list of keywords to listen to')
    parser.add_argument('--retweets', '-r', action='store_true', help='whether to include retweets')
    #parser.add_argument('--dbconnection', type=str, help='dbconnection to use to store the data')
    parser.add_argument('--out', '-o', type=str, help='filename for the file to save to')
    parser.add_argument('--mode', '-m', required='-q' not in sys.argv, type=str, choices=['stream', 'search'])
    parser.add_argument('--quota', '-q', action='store_true', help='output the remaining quota')
    parser.add_argument('--authfile', '-a', type=str, default='keys.yaml', help='path of the yaml containing the auth keys')
    args = parser.parse_args()

    api = TwitterAPI(**read_credentials(args.authfile))

    if args.quota:
        quota = get_quota(api)
        pprint.pprint(quota)
    else:
        with open(args.out if args.out else os.devnull) as f:
            for tweet in get_tweets(api, args.mode, args.keywords, retweets=args.retweets):
                logger.info(str(tweet))
                out.write(json.dumps(tweet))