import os
import urllib
import urllib.request
import logging
import json
from tqdm import tqdm
DICTIONARY_API = "https://linguee-api.herokuapp.com/api?q={}&src=nl&dst=en"

logging.basicConfig()
logger = logging.getLogger(__name__)



def load_words():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    words = []
    filename = os.path.join(base_dir, "vocabularies", "nederlands.txt")
    with open(filename, "r", encoding="ISO 8859-1") as dict_file:
        words += [word.strip() for word in dict_file.readlines()]
    return words


def parse_translation(word):
    description = ""	

    try:	
        url = DICTIONARY_API.format(word)
        logger.info(url)	
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
        pass
        #logger.exception(exc)	
    if description:
        return {word: description}	


def dump_dictionary(nederlands):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.join(base_dir, "1dictionary-nederlands.json")
    logger.info(f"dumping to {filename}")
    with open(filename, 'w') as file:
        json.dump(nederlands, file)
    return



if __name__ == "__main__":
    words = load_words()
    nederlands = {}

    for idx, word in enumerate(tqdm(words)):
        translation = parse_translation(word)
        if translation:
            nederlands.update(translation)
        if idx % 100 == 0:
            dump_dictionary(nederlands)

