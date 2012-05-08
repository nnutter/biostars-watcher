#!/usr/bin/env python

import argparse
import feedparser
import yaml
import json
from urlparse import urlparse
from jira.client import JIRA
from requests.auth import HTTPBasicAuth
from flask import Flask, render_template, jsonify


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


def connect_jira():
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


def issue_creation_data(entry):
    url = urlparse(entry.guid)
    post_id = find_post_id_from_url(url)
    fields = {
        'fields': {
            'labels': [
                'BioStars',
                post_id,
            ],
            'summary': entry.title,
            'description': "[Go to BioStars|http://biostars.org/post/show/{}/]".format(post_id),
            'project': {
                'key': config['jira']['project_key']
            },
            "issuetype": {
                "id": config['jira']['issue_type_id']
            },
        },
    }
    return json.dumps(fields)


def create_issue(jira, entry):
    payload = issue_creation_data(entry)
    rest_url = config['jira']['base_url'] + '/rest/api/2/issue'
    r = jira._session.post(rest_url, data=payload)
    data = json.loads(r.text)
    return jira.issue(data['key'])


def get_new_posts():
    jira = connect_jira()
    biostars_feed_url = config['biostars']['feed_url']
    d = feedparser.parse(biostars_feed_url)
    new_issues = []
    for entry in d.entries:
        if not jira_issue_exists(jira, entry):
            issue = create_issue(jira, entry)
            new_issues.append(issue)
    return new_issues


DEBUG = True
app = Flask(__name__)
app.config.from_object(__name__)


@app.route("/get_new_questions")
def get_new_questions():
    questions = []
    for issue in get_new_posts():
        questions.append(dict(
            summary=issue.fields.summary,
            url='http://biostars.org/post/show/{}/'.format(issue.key),
            jira_key=issue.key,
            jira_url='{}/browse/{}'.format(config['jira']['base_url'], issue.key),
        ))
    return jsonify(questions=questions)


@app.route("/get_questions")
def get_questions():
    jira = connect_jira()
    questions = []
    for issue in jira.search_issues('labels = BioStars AND status != Closed AND status != Resolved'):
        for label in issue.fields.labels:
            if not label == 'BioStars':
                biostar_key = label
        questions.append(dict(
            summary=issue.fields.summary,
            url='http://biostars.org/post/show/{}/'.format(biostar_key),
            jira_key=issue.key,
            jira_url='{}/browse/{}'.format(config['jira']['base_url'], issue.key),
        ))
    return jsonify(questions=questions)


@app.route("/")
def hello():
    return render_template('index.html')


if __name__ == '__main__':
    args = parse_args()
    global config
    config = load_config(args.c)
    app.run()
