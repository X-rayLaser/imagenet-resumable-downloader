import os
from concurrent.futures import ThreadPoolExecutor


# todo: download from config.json


class Config:
    def __init__(self,):
        self.app_data_folder = 'imagenet_data'

        self.wn_ids_path = os.path.join(self.app_data_folder,
                                        'word_net_ids.txt')

        self.registry_path = os.path.join(self.app_data_folder,
                                          'file-name-registry.json')

        self.download_state_path = os.path.join(self.app_data_folder,
                                                'download_state.json')

        self.synsets_url = (
            'http://www.image-net.org/api/text/imagenet.synset.obtain_synset_list'
        )

        self.word_net_ids_timeout = 120
        self.synsets_timeout = 120
        self.file_download_timeout = 1

        self.pool_executor = ThreadPoolExecutor(max_workers=100)

    def synset_urls_path(self, word_net_id):
        file_name = 'synset_urls_{}.txt'.format(word_net_id)
        return os.path.join(self.app_data_folder, file_name)

    def synset_download_url(self, word_net_id):
        return 'http://www.image-net.org/api/text/imagenet.synset.geturls?' \
               'wnid={}'.format(word_net_id)


config = Config()
