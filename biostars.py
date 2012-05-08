import json
from urlparse import urlparse


class Question:

    def __init__(self, title, urlstring, content):
        self.title = title
        self.urlstring = urlstring
        self.content = content

    def url(self):
        return urlparse(self.urlstring)

    def post_id(self):
        return self.url().path.split('/')[3]


class QuestionIssueMapper:

    def __init__(self, question, jira):
        self.question = question
        self.jira = jira

    def issue(self):
        jql_str = 'labels = BioStars AND labels = {}'.format(self.question.post_id())
        issues = self.jira.search_issues(jql_str=jql_str)
        if len(issues) > 1:
            raise Exception('Multiple Issues found for Question.')
        elif len(issues) == 0:
            raise Exception('No Issue found for Question.')
        else:
            return issues[0]

    def create_issue(self):
        # TODO get config?
        config = {}
        fields = {
            'fields': {
                'labels': [
                    'BioStars',
                    self.question.post_id(),
                ],
                'summary': self.question.title,
                'description': "[Go to BioStars|{}]".format(self.question.urlstring),
                'project': {
                    'key': config['jira']['project_key']
                },
                "issuetype": {
                    "id": config['jira']['issue_type_id']
                },
            },
        }
        payload = json.dumps(fields)
        rest_url = config['jira']['base_url'] + '/rest/api/2/issue'
        self.jira._session.post(rest_url, data=payload)
        return self.issue()
