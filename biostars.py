from urlparse import urlparse
import re


class Question:

    def __init__(self, title, urlstring=None, post_id=None, content=None):
        self.title = title
        self.content = content
        if urlstring == None and post_id == None:
            raise Exception('Question requires a post_id or a urlstring')
        if post_id != None:
            self.init_with_post_id(post_id)
            if self.post_id != post_id:
                raise Exception('provided post_id does not match urlstring')
        else:
            self.init_with_urlstring(urlstring)

    def init_with_post_id(self, post_id):
        urlstring = 'http://www.biostars.org/post/show/{}/'.format(post_id)
        self.init_with_urlstring(urlstring)

    def init_with_urlstring(self, urlstring):
        self.url = urlparse(urlstring)
        self.post_id = self.url.path.split('/')[3]
        if not re.match('^\d+$', self.post_id):
            raise Exception('post_id is not a number')
        if isinstance(self.post_id, unicode):
            self.post_id = str(self.post_id)

    def matches(self, pattern):
        for string in (self.title, self.content):
            if re.match(pattern, string, re.IGNORECASE):
                return True
        return False
