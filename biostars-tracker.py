#!/usr/bin/env python

from jira.client import JIRA
from requests.auth import HTTPBasicAuth
import argparse
import biostars
import feedparser
import json
import logging
import re
import time
import yaml


class BioStarsTracker:

    def __init__(self, config_path):
        self.questions = {}
        self.issues = {}
        self.last_post_id = -1
        self.config = yaml.load(file(config_path))
        self.connect_jira()

    def connect_jira(self):
        options = {
            'server': self.config['jira']['base_url'],
            'basic_auth': {
                'username': self.config['jira']['username'],
                'password': self.config['jira']['password'],
            },
        }
        jira = JIRA(options)
        auth_url = self.config['jira']['base_url'] + '/rest/auth/1/session'
        auth_data = HTTPBasicAuth(self.config['jira']['username'], self.config['jira']['password'])
        jira._session.get(auth_url, auth=auth_data)
        self.jira = jira

    def question_is_loaded(self, question):
        return question.post_id in self.questions

    def load_question(self, question):
        if question.post_id in self.questions:
            raise Exception('question already exists')
        self.questions[question.post_id] = question

    def load_known_questions(self):
        jql_str = 'project = "BST"'
        issues = self.jira.search_issues(jql_str=jql_str)
        for issue in issues:
            for label in issue.fields.labels:
                r = re.search('^BioStars-(\d)+$', label)
                if r != None:
                    question = biostars.Question(
                        title=issue.fields.summary,
                        post_id=r.group(1),
                    )
                    if not self.question_is_loaded(question):
                        self.load_question(question)

    def create_question_from_feed_entry(self, entry):
        return biostars.Question(
            title=entry.title,
            urlstring=entry.link,
            content=entry.description,
        )

    def load_new_questions(self):
        biostars_feed_url = self.config['biostars']['feed_url']
        biostars_feed = feedparser.parse(biostars_feed_url)

        # record last_post_id and return if same feed
        if len(biostars_feed.entries):
            question = self.create_question_from_feed_entry(biostars_feed.entries[0])
            if question.post_id == self.last_post_id:
                logging.debug('No new entries in feed.')
                return
            else:
                self.last_post_id = question.post_id

        for entry in biostars_feed.entries:
            question = self.create_question_from_feed_entry(entry)
            if question.matches('|'.join(self.config['biostars']['key_terms'])) and not self.question_is_loaded(question):
                logging.debug('loading question')
                self.load_question(question)

        return True

    def issue_for_post_id(self, post_id):
        jql_str = 'project = "BST" AND labels = BioStars-{}'.format(post_id)
        issues = self.jira.search_issues(jql_str=jql_str)
        if len(issues) > 1:
            raise Exception('multiple issues found')
        if len(issues) == 1:
            return issues[0]
        else:
            return False

    def map_issues(self):
        for post_id in self.questions.keys():
            issue = self.issue_for_post_id(post_id)
            if issue:
                logging.info('POST_ID = {}, KEY = {}'.format(post_id, issue.key))
            else:
                logging.info('POST_ID = {}, KEY = MISSING'.format(post_id))
                qi_map = QuestionIssueMap(question=self.questions[post_id], jira=self.jira, config=self.config)
                qi_map.create_issue()

    def main(self):
        self.load_known_questions()
        while True:
            if self.load_new_questions():
                self.map_issues()
            time.sleep(5)


class QuestionIssueMap:

    def __init__(self, question=None, jira=None, config=None):
        self.question = question
        self.jira = jira
        self.config = config

    def issue(self):
        jql_str = 'project = "BST" AND labels = BioStars-{}'.format(self.question.post_id)
        issues = self.jira.search_issues(jql_str=jql_str)
        if len(issues) > 1:
            raise Exception('Multiple Issues found for Question.')
        elif len(issues) == 0:
            raise Exception('No Issue found for Question.')
        else:
            return issues[0]

    def create_issue(self):
        fields = {
            'fields': {
                'labels': [
                    'BioStars-{}'.format(self.question.post_id),
                ],
                'summary': self.question.title,
                'description': "[Go to BioStars|{}]".format(self.question.urlstring),
                'project': {
                    'key': self.config['jira']['project_key']
                },
                "issuetype": {
                    "id": self.config['jira']['issue_type_id']
                },
            },
        }
        payload = json.dumps(fields)
        rest_url = self.config['jira']['base_url'] + '/rest/api/2/issue'
        self.jira._session.post(rest_url, data=payload)
        return self.issue()


def parse_args():
    parser = argparse.ArgumentParser(
        prog='biostars-watcher.py',
    )
    parser.add_argument('-c', '--config', default='config.yaml', help='config file')
    parser.add_argument('-d', '--debug', action='store_true', help='enable debug messages')

    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parse_args()
    tracker = BioStarsTracker(config_path=args.config)
    if args.debug:
        logging.basicConfig(
            format='%(levelname)s: %(message)s',
            level=logging.DEBUG,
        )
        logging.debug('Debug logging enabled')
    tracker.main()
