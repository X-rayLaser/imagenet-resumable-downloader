import unittest
import sys
sys.path.insert(0, './')

from registered_test_cases import Meta
import util


class Url2FileNameTests(unittest.TestCase, metaclass=Meta):
    def test_conversion_of_first_urls(self):
        url2name = util.Url2FileName()
        first = url2name.convert('http://haha.com/hahahaha.jpg')
        second = url2name.convert('http://example.com/hahahaha.png')
        self.assertEqual(first, '1.jpg')
        self.assertEqual(second, '2.png')

    def test_that_urls_with_trailing_newline_are_forbidden(self):
        url2name = util.Url2FileName()

        def f1():
            url2name.convert('http://haha.com/hahahaha.jpg\n')

        def f2():
            url2name.convert('http://haha.com/hahahaha.jpg\n\r\n\r')

        self.assertRaises(util.MalformedUrlError, f1)

        self.assertRaises(util.MalformedUrlError, f2)

        first = url2name.convert('http://haha.com/hahahaha.jpg')
        self.assertEqual(first, '1.jpg')

    def test_that_urls_with_trailing_spaces_are_forbidden(self):
        url2name = util.Url2FileName()

        def f():
            url2name.convert('http://haha.com/hahahaha.jpg    \n')

        self.assertRaises(util.MalformedUrlError, f)

        first = url2name.convert('http://haha.com/hahahaha.jpg')
        self.assertEqual(first, '1.jpg')

    def test_that_conversion_accounts_for_duplicates(self):
        url2name = util.Url2FileName()
        first = url2name.convert('http://example.com/xyz.jpg')
        second = url2name.convert('http://example.com/xyz.jpg')
        self.assertEqual(first, '1.jpg')
        self.assertEqual(second, '2.jpg')

    def test_with_non_ascii_characters_in_url_file_path(self):
        url2name = util.Url2FileName()

        from urllib import parse
        path = parse.quote(' xyz~`!@#$%^&*()_+=-{}[];:\'"\|,.<>/?.jpg')
        first = url2name.convert(
            'http://example.com/' + path
        )

        self.assertEqual(first, '1.jpg')

    def test_starting_index(self):
        url2name = util.Url2FileName(starting_index=3)
        self.assertEqual(url2name.file_index, 3)

        third = url2name.convert('http://example.com/third.gif')
        fourth = url2name.convert('http://example.com/fourth.png')

        self.assertEqual(third, '3.gif')
        self.assertEqual(fourth, '4.png')

        self.assertEqual(url2name.file_index, 5)
