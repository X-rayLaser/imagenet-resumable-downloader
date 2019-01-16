import unittest
import os
import sys

sys.path.insert(0, './')
from downloader import WordNetIdList, Synset, ItemsRegistry


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


class FileNameRegistryTests(unittest.TestCase):
    def setUp(self):
        file_dir = 'imagenet_data'
        file_path = os.path.join(file_dir, 'test_registry.json')
        self.file_path = file_path

        if not os.path.exists(file_dir):
            os.mkdir(file_dir)

        if os.path.isfile(file_path):
            os.remove(file_path)
        self.registry = ItemsRegistry(file_path)

    def test_adding_name_and_checking_it(self):
        registry = self.registry
        self.assertNotIn('Hello, world!', registry)
        registry.add('Hello, world!')
        self.assertIn('Hello, world!', registry)

    def test_items_persist(self):
        registry = self.registry
        registry.add('first')
        registry.add('second')
        registry.add('third')
        registry.remove('second')
        
        registry = ItemsRegistry(self.file_path)
        self.assertIn('first', registry)
        self.assertIn('third', registry)
        self.assertNotIn('second', registry)

    def test_numbers_persist(self):
        registry = self.registry
        registry.add(2)
        registry.add(9)
        registry.add(11)
        registry.remove(9)

        registry = ItemsRegistry(self.file_path)
        self.assertIn(2, registry)
        self.assertIn(11, registry)
        self.assertNotIn(9, registry)

    def test_add_after_loading_from_file(self):
        registry = self.registry
        registry.add(2)
        registry.add("Hello")

        registry = ItemsRegistry(self.file_path)
        registry.add('world')

        self.assertIn(2, registry)
        self.assertIn('Hello', registry)
        self.assertIn('world', registry)

    def test_remove_after_loading_from_file(self):
        registry = self.registry
        registry.add(2)
        registry.add("Hello")

        registry = ItemsRegistry(self.file_path)
        registry.remove("Hello")
        self.assertIn(2, registry)
        self.assertNotIn("hello", registry)

    def test_adding_2_items(self):
        registry = self.registry
        registry.add('First')
        registry.add('Second')
        self.assertIn('First', registry)
        self.assertIn('Second', registry)

    def test_item_removal(self):
        registry = self.registry
        registry.add('First')
        registry.remove('First')
        self.assertNotIn('First', registry)

    def test_removal_of_missing_item_has_no_effect(self):
        registry = self.registry
        registry.add('First')
        registry.remove('Second')

        self.assertIn('First', registry)
        self.assertNotIn('Second', registry)


class Url2FileNameTests(unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main()
