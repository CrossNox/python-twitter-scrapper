#!/usr/bin/env python3

import yaml
from TwitterAPI import TwitterAPI, TwitterRequestError, TwitterConnectionError
import argparse
import logging
import os
import json
import sys
from pprint import pprint
import datetime
import time
import click

logging.basicConfig(
    format='%(levelname)s %(asctime)s: %(message)s',
    level=logging.INFO
)
log = logging.getLogger(__name__)


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


def search_filter(tweet, retweets):
    return True


def stream_filter(tweet, retweets):
    if retweets:
        return True
    return 'retweeted_status' not in tweet


def get_search_next_window_start(api):
    r = api.request('application/rate_limit_status').json()
    return datetime.datetime.fromtimestamp(r['resources']['search']['/search/tweets']['reset'])


def get_tweets(api, mode, keywords, retweets=False):
    log.info("mode: {}, keywords: {}, retweets: {}".format(mode, keywords, retweets))
    params = {KW_QS[mode]: keywords}
    if mode == 'search' and not retweets:
        params['-filter'] = 'retweets'
    tweet_filter = search_filter if mode == 'search' else stream_filter
    while True:
        try:
            r = api.request(ENDPOINTS[mode], params).get_iterator()
            for item in r:
                if tweet_filter(item, retweets):
                    yield item
        except TwitterRequestError as e:
            if e.status_code >= 500:
                time.sleep(5)
            elif e.status_code == 429 and mode=='search':
                log.info("request limit reached")
                while True:
                    now = datetime.datetime.now()
                    next_window = get_search_next_window_start(api)
                    sleep_time = (next_window - now).total_seconds()
                    log.info("sleeping {} seconds until next window start @ {}".format(
                            sleep_time,
                            next_window
                        ))
                    time.sleep(min(120, sleep_time))
            else:
                raise
        except TwitterConnectionError:
            time.sleep(5)


def get_quota(api):
    r = api.request('application/rate_limit_status').json()
    search_quota = r['resources']['search']['/search/tweets']
    search_quota['reset'] = datetime.datetime.fromtimestamp(
        search_quota['reset']
    ).strftime('%Y-%m-%d %H:%M:%S')
    return {'search_quota': search_quota}


if __name__ == "__main__":
    mode_required = '-q' not in sys.argv and '--quota' not in sys.argv

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--keywords', '-k', required=mode_required, nargs='+', help='list of keywords to listen to')
    parser.add_argument('--retweets', '-r', required=False, action='store_true', help='whether to include retweets')
    #parser.add_argument('--dbconnection', type=str, help='dbconnection to use to store the data')
    parser.add_argument('--out', '-o', type=str, help='filename for the file to save to')
    parser.add_argument('--mode', '-m', required=mode_required, type=str, choices=['stream', 'search'], help='twitter mode')
    parser.add_argument('--quota', '-q', action='store_true', help='output the remaining quota')
    parser.add_argument('--authfile', '-a', type=str, default='keys.yaml', help='path of the yaml containing the auth keys')
    parser.add_argument('--limit', '-l', type=int, help='max number of tweets to retrieve (0 indicates no limit)', default=0)
    args = parser.parse_args()

    api = TwitterAPI(**read_credentials(args.authfile))

    if args.quota:
        quota = get_quota(api)
        pprint(quota)
    else:
        log.info("Starting scrapper on {} mode".format(args.mode))
        if args.out:
            log.info("Writing tweets to {}".format(args.out))

        # if no out file was passed, output is discarded
        if args.out and not args.out.endswith('.json'):
            args.out += '.json'

        overwrite = False
        if os.path.isfile(args.out):
            if click.confirm('file {} already exists. Overwrite?'.format(args.out), default=True):
                overwrite = True
        flag = 'w' if overwrite else 'a'

        with open(args.out if args.out else os.devnull, flag) as out:
            i = 0
            try:
                for tweet in get_tweets(api, args.mode, args.keywords, retweets=args.retweets):
                    out.write(json.dumps(tweet))
                    out.write(os.linesep)
                    i += 1
                    if args.limit != 0 and args.limit == i:
                        break
                    log.info("{} tweets retrieved so far".format(i))
            except KeyboardInterrupt:
                log.info("ending scrapper by user interrupt")
