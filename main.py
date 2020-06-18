import re
import os
import json
import glob
import logging
from time import sleep
from ulauncher.search.SortedList import SortedList
from ulauncher.utils.SortedCollection import SortedCollection
from ulauncher.api.client.Extension import Extension, PreferencesEventListener
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent, PreferencesEvent, PreferencesUpdateEvent

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


def load_words(vocabularies):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    words = []
    for vocabulary in vocabularies:
        filename = os.path.join(base_dir, "vocabularies", "{}.txt".format(vocabulary))
        with open(filename, "r", encoding="ISO 8859-1") as dict_file:
            words += [Word(word.strip(), vocabulary) for word in dict_file.readlines()]
    return words



class OneDictExtension(Extension):

    def __init__(self):
        super(OneDictExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())

        self.word_list = []

    def run(self):
        self.subscribe(PreferencesEvent, PreferencesEventListener())
        self.subscribe(PreferencesUpdateEvent, PreferencesUpdateEventListener())
        self._client.connect()


class PreferencesEventListener(EventListener):
    def on_event(self, event, extension):
        extension.preferences.update(event.preferences)

        vocabularies = [voc.rstrip().lstrip() for voc in extension.preferences["vocabulary"].split(',')]
        extension.word_list = load_words(vocabularies)



class PreferencesUpdateEventListener(EventListener):

    def on_event(self, event, extension):
        extension.preferences[event.id] = event.new_value

        vocabularies = [voc.rstrip().lstrip() for voc in extension.preferences["vocabulary"].split(',')]
        extension.word_list = load_words(vocabularies)


class KeywordQueryEventListener(EventListener):

    def on_event(self, event, extension):
        items = []
        query = event.get_argument()
        if query:
            dictionaries = {}
            for row in extension.preferences["online_dictionary"].split(';'):
                try:
                    lang, url = row.split(',')
                    dictionaries[lang.rstrip().lstrip()] = url.rstrip().lstrip()
                except ValueError as ve:
                    logger.exception(ve)

            if extension.preferences["matching"] == "regex":
                result_list = [w for w in extension.word_list if re.search(r'^{}'.format(query), w.get_search_name())]
            else:
                result_list = CustomSortedList(query, min_score=60)
                result_list.extend(extension.word_list)

            for result in result_list[:9]:
                word, language = str(result).split('/')

                items.append(ExtensionResultItem(
                    icon='images/icon.png',
                    name=word,
                    description="Language: {}".format(language),
                    on_enter=OpenUrlAction(dictionaries.get(language, DEFAULT_DICTIONARY) % word)))

        else:
            items.append(ExtensionResultItem(
                icon='images/icon.png',
                name="Type in the word...",
                description="",
                ))

        return RenderResultListAction(items)


class ItemEnterEventListener(EventListener):

    def on_event(self, event, extension):
        data = event.get_data()
        return RenderResultListAction([ExtensionResultItem(icon='images/icon.png',
                                                           name=data['new_name'],
                                                           on_enter=HideWindowAction())])



class CustomSortedList(SortedList):
    def __init__(self, query, min_score):
        super(CustomSortedList, self).__init__(query, min_score, limit=9)
        self._items = SortedCollection(key=lambda i: (i.score, abs(len(self._query) - len(i.get_search_name()))))


if __name__ == '__main__':
    OneDictExtension().run()
