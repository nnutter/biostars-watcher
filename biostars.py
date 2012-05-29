from urlparse import urlparse
import re


class Question:

    def __init__(self, title, urlstring=None, post_id=None, content=None):
        self.title = title
        self.content = content

        if urlstring == None and post_id == None:
            raise Exception('Question requires a post_id or a urlstring.')

        if urlstring != None:
            self.urlstring = urlstring
            self.url = urlparse(urlstring)
        elif post_id != None:
            self.urlstring = 'http://www.biostars.org/post/show/{}/'.format(post_id)
            self.url = urlparse(self.urlstring)

        self.post_id = self.url.path.split('/')[3]
        if post_id != None and self.post_id != post_id:
            raise Exception('provided post_id is not consistent with urlstring')

        if not re.match('^\d+$', self.post_id):
            raise Exception('post_id({}) is not a number'.format(self.post_id))

        if isinstance(self.post_id, unicode):
            self.post_id = str(self.post_id)

    def matches(self, pattern):
        for string in (self.title, self.content):
            if re.match(pattern, string, re.IGNORECASE):
                return True
        return False
