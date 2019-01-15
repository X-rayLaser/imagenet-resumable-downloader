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
        for wn_id in synset:
            self.assertFalse('\n' in wn_id, 'Contains "\n" character')


if __name__ == '__main__':
    unittest.main()
