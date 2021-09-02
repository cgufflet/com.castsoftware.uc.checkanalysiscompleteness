import os
from collections import defaultdict
from functools import lru_cache
from linguist.languages import languages


@lru_cache()
def build_extension_to_languages():
    """
    @rtype: dict(list(str,dict))
    """
    result = defaultdict(list)
    for language, data in languages.items():

        # versatility
        if "primary_extension" in data:
            result[data["primary_extension"]].append((language, data))

        if 'extensions' in data:

            for ext in data['extensions']:
                result[ext].append((language, data))

    return result


@lru_cache()
def build_filename_to_languages():
    """
    @rtype: dict(list(str,dict))
    """
    result = defaultdict(list)
    for language, data in languages.items():

        try:
            for filename in data["filenames"]:
                result[filename].append((language, data))

        except KeyError:
            pass

    return result


def recognise_language(filepath):
    """
    Return a list of languages recognized by extensions.

    Inspired from https://github.com/liluo/linguist

    @rtype: list(str,dict)

    @todo: handle filenames...
    """
    filename = os.path.basename(filepath)
    filename_map = build_filename_to_languages()

    if filename in filename_map:
        return filename_map[filename]

    ext = os.path.splitext(filepath)[1].lower()

    language_map = build_extension_to_languages()

    return language_map[ext]


def get_language_type(language):
    try:
        return languages[language]["type"]
    except KeyError:

        if language in ['PLSQL (uax)', 'Sybase (uax)', 'SQLServer (uax)', 'Forms (uax)']:
            return "programming"

        return "unknown"


def get_primary_file_extension(language):
    try:
        return languages[language]["primary_extension"]
    except KeyError:
        return "unknown"

def is_web_front(filepath):
    """
    True when the filepath is of a web front language.
    """
    try:
        language = recognise_language(filepath)[0][0]

        # do not contain javascript/typescript due to the fact we do not
        # know here if it is front or back
        web_languages = ['HTML', 'JSP', 'ASP', 'PHP', 'CSS', 'CoffeeScript']

        if language in web_languages:
            return True

        try:
            group = languages[language]["group"]
            if group in web_languages:
                return True
        except KeyError:
            pass
    except IndexError:
        pass

    return False
