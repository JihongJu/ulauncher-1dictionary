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


class Word:
    def __init__(self, word):
        self._word = word


    def __repr__(self):
        return self._word

    def get_search_name(self):
        return self._word


def load_words(dict_name):
    dict_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(dict_path, dict_name), "r", encoding="ISO 8859-1") as dict_file:
        words = [Word(word.strip()) for word in dict_file.readlines()]
    return words



class OneDictExtension(Extension):

    def __init__(self):
        super(OneDictExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())

        self.word_list = load_words("1vocabulary.txt")


class KeywordQueryEventListener(EventListener):

    def on_event(self, event, extension):
        items = []
        query = event.get_argument()
        if query:
            result_list = SortedList(query, min_score=80, limit=100)
            result_list.extend(extension.word_list)

            for word in sort_list(result_list, query)[:9]:
                description = ""
                items.append(ExtensionResultItem(
                    icon='images/icon.png',
                    name=str(word),
                    description=description,
                    on_enter=OpenUrlAction(
                        extension.preferences["online_dictionary"] % str(word))))

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
