import os
import json
import glob
import logging
from time import sleep
from ulauncher.search.SortedList import SortedList
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent

from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.OpenUrlAction import OpenUrlAction

from ulauncher.utils.fuzzy_search import get_score


logging.basicConfig()
logger = logging.getLogger(__name__)


DEFAULT_DICTIONARY="https://translate.google.com/#view=home&op=translate&sl=auto&tl=en&text=%s"


class Word:
    def __init__(self, word, vocabulary):
        self._word = word
        self._vocabulary = vocabulary


    def __repr__(self):
        return "{}/{}".format(self._word, self._vocabulary)

    def get_search_name(self):
        return self._word


def load_words():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    words = []
    for vocabulary in glob.glob("{}/*.txt".format(base_dir)):
        name, *_ = os.path.basename(vocabulary).split('.')
        with open(vocabulary, "r", encoding="ISO 8859-1") as dict_file:
            words += [Word(word.strip(), name) for word in dict_file.readlines()]
    return words



class OneDictExtension(Extension):

    def __init__(self):
        super(OneDictExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())

        self.word_list = load_words()


class KeywordQueryEventListener(EventListener):

    def on_event(self, event, extension):
        items = []
        query = event.get_argument()
        if query:
            result_list = SortedList(query, min_score=40, limit=40)
            result_list.extend(extension.word_list)

            dictionaries = {}
            for row in extension.preferences["online_dictionary"].split(';'):
                lang, url = row.split(',')
                dictionaries[lang.rstrip().lstrip()] = url.rstrip().lstrip()


            for result in sort_list(result_list, query)[:9]:
                word, language = str(result).split('/')

                items.append(ExtensionResultItem(
                    icon='images/icon.png',
                    name=word,
                    description="Language: {}".format(language),
                    on_enter=OpenUrlAction(dictionaries.get(language, DEFAULT_DICTIONARY) % word)))

        return RenderResultListAction(items)


class ItemEnterEventListener(EventListener):

    def on_event(self, event, extension):
        data = event.get_data()
        return RenderResultListAction([ExtensionResultItem(icon='images/icon.png',
                                                           name=data['new_name'],
                                                           on_enter=HideWindowAction())])


def sort_list(result_list, query):
    return sorted(result_list, key=lambda w: (-get_score(query, w.get_search_name()), len(str(w))))


if __name__ == '__main__':
    OneDictExtension().run()
