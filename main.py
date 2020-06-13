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

logging.basicConfig()
logger = logging.getLogger(__name__)



class Word:
    def __init__(self, word):
        self._word = word


    def __str__(self):
        return self._word

    def get_search_name(self):
        return self._word


def load_words():
    with open("nederlands.txt", "r", encoding="ISO 8859-1") as dict_file:
        words = [Word(word.strip()) for word in dict_file.readlines()]
    return words




class DemoExtension(Extension):

    def __init__(self):
        super(DemoExtension, self).__init__()
        self.word_list = load_words()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())


class KeywordQueryEventListener(EventListener):

    def on_event(self, event, extension):
        items = []
        logger.info('preferences %s' % json.dumps(extension.preferences))
        query = event.get_argument()
        if query:
            result_list = SortedList(query, min_score=40, limit=10)
            result_list.extend(extension.word_list)

            for word in result_list:
                data = {'new_name': '%s  was clicked' % (word)}
                items.append(ExtensionResultItem(
                    icon='images/icon.png',
                    name='%s' % (word),
                    description='Item description %s' % word,
                    on_enter=OpenUrlAction(
                        'https://www.linguee.com/dutch-english/search?source=auto&query={}'.format(word))))

        return RenderResultListAction(items)


class ItemEnterEventListener(EventListener):

    def on_event(self, event, extension):
        data = event.get_data()
        return RenderResultListAction([ExtensionResultItem(icon='images/icon.png',
                                                           name=data['new_name'],
                                                           on_enter=HideWindowAction())])


if __name__ == '__main__':
    DemoExtension().run()
