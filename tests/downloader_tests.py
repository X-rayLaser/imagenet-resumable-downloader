import unittest
import os
import sys

sys.path.insert(0, './')
from downloader import WordNetIdList, Synset


class WordNetIdListTests(unittest.TestCase):
    def test_word_net_id_has_no_trailing_newline_character(self):
        wordnet_ids_list = WordNetIdList('tests/wordnet_ids_fixture.txt')
        for wn_id in wordnet_ids_list:
            self.assertFalse('\n' in wn_id, 'Contains "\n" character')

    def test_that_iterator_outputs_expected_wn_id_values(self):
        wordnet_ids_list = WordNetIdList('tests/wordnet_ids_fixture.txt')
        ids = [wn_id for wn_id in wordnet_ids_list]

        self.assertEqual(ids[0], 'n02119789')
        self.assertEqual(ids[1], 'n02478875')


class SynsetTests(unittest.TestCase):
    def test_url_has_no_trailing_newline_character(self):
        synset = Synset(wn_id='wn_id_fixture')
        for url in synset:
            self.assertFalse('\n' in url, 'Contains "\n" character')

    def test_that_iterator_outputs_expected_urls(self):
        synset = Synset(wn_id='wn_id_fixture')
        urls = [url for url in synset]
        self.assertEqual(urls[0], 'http://some_domain.com/something')
        self.assertEqual(urls[1], 'http://another-domain.com/1234%329jflija')
        self.assertEqual(urls[2], 'http://another-domain.com/x/y/z')

    def test_batch_iterator(self):
        synset = Synset(wn_id='wn_id_fixture')

        batches = [batch for batch in synset.get_url_batches(size=2)]
        self.assertEqual(len(batches), 2)

        urls = [url for url in batches[0]]
        self.assertEqual(len(urls), 2)
        self.assertEqual(urls[0], 'http://some_domain.com/something')
        self.assertEqual(urls[1], 'http://another-domain.com/1234%329jflija')

        urls = [url for url in batches[1]]
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0], 'http://another-domain.com/x/y/z')


if __name__ == '__main__':
    unittest.main()
