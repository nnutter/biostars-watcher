import feedparser
import yaml
from urlparse import urlparse
from jira.client import JIRA


def list_issues():
    config_file = file('config.yaml')
    config = yaml.load(config_file)
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


def list_posts():
    d = feedparser.parse('http://www.biostars.org/feeds/tag/tigra+breakdancer')
    for entry in d.entries:
        url = urlparse(entry.guid)
        post_id = find_post_id_from_url(url)
        print("POST: (%s) %s" % (post_id, entry.title))


if __name__ == '__main__':
    list_issues()
    list_posts()
