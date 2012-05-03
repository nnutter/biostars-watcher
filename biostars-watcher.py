#!/usr/bin/env python

import argparse
import feedparser
import yaml
import json
from urlparse import urlparse
from jira.client import JIRA
from requests.auth import HTTPBasicAuth


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


def jira_issue_exists(jira, entry):
    url = urlparse(entry.guid)
    post_id = find_post_id_from_url(url)
    issues = jira.search_issues(jql_str='labels = BioStars AND labels = ' + post_id)
    if len(issues) > 0:
        return True
    else:
        return False


def connect_jira(config):
    options = {
        'server': config['jira']['base_url'],
        'basic_auth': {
            'username': config['jira']['username'],
            'password': config['jira']['password'],
        },
    }
    jira = JIRA(options)
    auth_url = config['jira']['base_url'] + '/rest/auth/1/session'
    auth_data = HTTPBasicAuth(config['jira']['username'], config['jira']['password'])
    jira._session.get(auth_url, auth=auth_data)
    return jira


def find_post_id_from_url(url):
    path = url.path
    post_id = path.split('/')[3]
    return post_id


def issue_creation_data(config, entry):
    url = urlparse(entry.guid)
    post_id = find_post_id_from_url(url)
    fields = {
        'fields': {
            'labels': [
                'BioStars',
                post_id,
            ],
            'summary': entry.title,
            'description': entry.description,
            'project': {
                'key': config['jira']['project_key']
            },
            "issuetype": {
                "id": config['jira']['issue_type_id']
            },
        },
    }
    return json.dumps(fields)


def create_issue(jira, entry, config):
    payload = issue_creation_data(config, entry)
    rest_url = config['jira']['base_url'] + '/rest/api/2/issue'
    r = jira._session.post(rest_url, data=payload)
    print r.text


def check_posts(config):
    jira = connect_jira(config)
    biostars_feed_url = config['biostars']['feed_url']
    d = feedparser.parse(biostars_feed_url)
    for entry in d.entries:
        if not jira_issue_exists(jira, entry):
            create_issue(jira, entry, config)


if __name__ == '__main__':
    args = parse_args()
    config = load_config(args.c)
    check_posts(config)
