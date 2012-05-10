import biostars
import unittest
import urlparse


class TestQuestionFunctions(unittest.TestCase):

    def setUp(self):
        self.question = biostars.Question(
            title='This Is Quite the Title!',
            urlstring='http://www.biostars.org/post/show/99999/this-is-quite-the-title/',
            content='This, however, is quite a boring content...',
        )

    def test_post_id(self):
        self.assertEqual(self.question.post_id, '99999')

    # This is a silly test.
    def test_url(self):
        self.assertIsInstance(self.question.url, urlparse.ParseResult)


if __name__ == '__main__':
    unittest.main()
