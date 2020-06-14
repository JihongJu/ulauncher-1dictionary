import re
import os
import json
import glob
import logging
import urllib	
import urllib.request
from time import sleep
from ulauncher.search.SortedList import SortedList
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
DICTIONARY_API = "https://linguee-api.herokuapp.com/api?q={}&src=nl&dst=en"


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
        filename = os.path.join(base_dir, "{}.txt".format(vocabulary))
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
            if extension.preferences["matching"] == "regex":
                result_list = [w for w in extension.word_list if re.search(r'^{}'.format(query), w.get_search_name())]
            else:
                result_list = SortedList(query, min_score=40, limit=40)
                result_list.extend(extension.word_list)

            dictionaries = {}
            for row in extension.preferences["online_dictionary"].split(';'):
                try:
                    lang, url = row.split(',')
                    dictionaries[lang.rstrip().lstrip()] = url.rstrip().lstrip()
                except ValueError as ve:
                    logger.exception(ve)


            for result in sort_list(result_list, query)[:9]:
                word, language = str(result).split('/')

                description = "Language: {}".format(language)
                if str(word) == query and language == "nederlands":	
                    translation = translation_as_description(DICTIONARY_API.format(word))
                    if translation:
                        description = translation

                items.append(ExtensionResultItem(
                    icon='images/icon.png',
                    name=word,
                    description=description,
                    on_enter=OpenUrlAction(dictionaries.get(language, DEFAULT_DICTIONARY) % word)))

        return RenderResultListAction(items)


class ItemEnterEventListener(EventListener):

    def on_event(self, event, extension):
        data = event.get_data()
        return RenderResultListAction([ExtensionResultItem(icon='images/icon.png',
                                                           name=data['new_name'],
                                                           on_enter=HideWindowAction())])


def sort_list(result_list, query):
    return sorted(result_list, key=lambda w: (-get_score(query, w.get_search_name()), len(w.get_search_name())))



def translation_as_description(url):	
    description = ""	
    logger.info(url)	

    try:	
        resp = urllib.request.urlopen(url)	
        if str(resp.getcode()).startswith('2'):	
            data=resp.read()	
            encoding=resp.info().get_content_charset("utf-8")	
            payload=json.loads(data.decode(encoding))	

            if payload["exact_matches"]:	
                description += "[nl]"
                for idx, match in enumerate(payload["exact_matches"]):
                    word_type = match.get("word_type", {})	
                    description += " {}.".format(idx)
                    pos = word_type.get("pos", None)	
                    if pos:	
                        description += "{}".format(pos)	
                    gender = word_type.get("gender", None)	
                    if gender:	
                        description += " ({})".format(gender)	
                    description += ": "	

                    translations = match.get("translations", None)	
                    if translations:	
                        description += ",".join([entry["text"] for entry in translations])	

                    description += ";"	
    except Exception as exc:	
        logger.exception(exc)	
    return description	



if __name__ == '__main__':
    OneDictExtension().run()
