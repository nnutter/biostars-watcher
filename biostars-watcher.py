#!/usr/bin/env python

import argparse
import feedparser
import yaml
from urlparse import urlparse
from jira.client import JIRA


def parse_args():
    parser = argparse.ArgumentParser(
        prog='biostars-watcher.py',
    )
    parser.add_argument('-c', default='config.yaml', help='a config file')

    args = parser.parse_args()
    return args


def load_config(config_file_path):
    config_file = file(config_file_path)
    config = yaml.load(config_file)
    return config


def list_issues(config_file_path):
    config = load_config(config_file_path)
    options = {
        'server': config['jira_server_base_url'],
        'basic_auth': {
            'username': config['username'],
            'password': config['password'],
        },
    }
    jira = JIRA(options)
    issues = jira.search_issues(jql_str=config['jql_query'])
    for issue in issues:
        print("ISSUE: %s" % (issue.fields.summary))


def find_post_id_from_url(url):
    path = url.path
    post_id = path.split('/')[3]
    return post_id


def list_posts(config_file_path):
    config = load_config(config_file_path)
    biostars_feed_url = config['biostars_feed_url']
    d = feedparser.parse(biostars_feed_url)
    for entry in d.entries:
        url = urlparse(entry.guid)
        post_id = find_post_id_from_url(url)
        print("POST: (%s) %s" % (post_id, entry.title))


if __name__ == '__main__':
    args = parse_args()
    list_issues(args.c)
    list_posts(args.c)
