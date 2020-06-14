import os
import urllib
import urllib.request
import json
import logging
import pickle
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


DICTIONRARY_ONLINE = "https://www.linguee.com/dutch-english/search?source=auto&query={}"
DICTIONARY_API = "https://linguee-api.herokuapp.com/api?q={}&src=nl&dst=en"


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



class DemoExtension(Extension):

    def __init__(self):
        super(DemoExtension, self).__init__()
        self.word_list = load_words("nederlands.txt")
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())


class KeywordQueryEventListener(EventListener):

    def on_event(self, event, extension):
        items = []
        logger.info('preferences %s' % json.dumps(extension.preferences))
        query = event.get_argument()
        if query:
            result_list = SortedList(query, min_score=80, limit=100)
            result_list.extend(extension.word_list)

            for word in sort_list(result_list, query)[:9]:
                description = ""
                if str(word) == query:
                    description = translation_as_description(DICTIONARY_API.format(str(word)))
                items.append(ExtensionResultItem(
                    icon='images/icon.png',
                    name=str(word),
                    description=description,
                    on_enter=OpenUrlAction(
                        DICTIONRARY_ONLINE.format(str(word)))))

        return RenderResultListAction(items)


class ItemEnterEventListener(EventListener):

    def on_event(self, event, extension):
        data = event.get_data()
        return RenderResultListAction([ExtensionResultItem(icon='images/icon.png',
                                                           name=data['new_name'],
                                                           on_enter=HideWindowAction())])


def sort_list(result_list, query):
    return sorted(result_list, key=lambda w: (-get_score(query, w.get_search_name()), len(str(w))))


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
                for match in payload["exact_matches"]:
                    word_type = match.get("word_type", {})
                    pos = word_type.get("pos", None)
                    if pos:
                        description += " {}".format(pos)
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
    DemoExtension().run()
