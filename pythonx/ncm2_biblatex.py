# -*- coding: utf-8 -*-

import os
import re
# from glob import glob
from bibparse import Biblio, BibError
from ncm2 import Ncm2Source, getLogger
import vim

logger = getLogger(__name__)


class Source(Ncm2Source):
    def __init__(self, vim):
        super(Source, self).__init__(vim)
        self.vim = vim

        # Path of bibfile:
        self.__bib_file = self.__get_variable("ncm2_biblatex#bibfile",
                                              "~/bibliography.bib")
        self.__glob_re = re.compile(r"\*")

        self.__bib_files = []
        if isinstance(self.__bib_file, list):
            for file in self.__bib_file:
                self.__bib_files.append(os.path.abspath(file))
        else:
            self.__bib_files.append(os.path.abspath(self.__bib_file))

        # Cache bibfile:
        # self.__bib_file_mtime = os.stat(self.__bib_file).st_mtime
        self.__bib_files_mtimes = {}
        for file in self.__bib_files:
            self.__bib_files_mtimes[file] = os.stat(file).st_mtime

        self.__cached_biblio = None

        # Reload bibliography on change?
        self.__reload_bibliography_on_change = bool(
            self.__get_variable("ncm2_biblatex#reloadbibfileonchange", 0))

        # Add info?
        self.__add_info = bool(self.__get_variable("ncm2_biblatex#addinfo", 0))

        # Hunt for keys within the larger match:
        self.__key_pattern = re.compile(r"[\w-]+")

    def __get_variable(self, key, default):
        return self.vim.eval("get(g:, '{}', '{}')".format(key, default))

    def on_warmup(self, _context):
        self.__read_biblio()

    def __read_biblio(self):
        self.__cached_biblio = Biblio()
        for file in self.__bib_files:
            try:
                self.__cached_biblio.read(file)
            except BibError as err:
                print(err)

    @property
    def __biblio(self):
        # if False:
        if self.__reload_bibliography_on_change:
            for file in self.__bib_files:
                mtime = os.stat(file).st_mtime

                if mtime != self.__bib_files_mtimes[file]:
                    self.__bib_files_mtimes[file] = mtime
                    self.__read_biblio()

        return self.__cached_biblio

    @staticmethod
    def __format_info(entry):
        return "{title}{author}{date}".format(
            title=("Title: {}\n".format(re.sub(r"[}{]", "", entry["title"]))
                   if "title" in entry else ""),
            author=("Author{plural}: {author}\n".format(
                plural="s" if len(entry["author"]) > 1 else "",
                author="; ".join(entry["author"]),
            ) if "author" in entry else ""),
            date=("Year: {}\n".format(entry["date"].split("-")[0])
                  if "date" in entry else ""),
        )

    def __format_candidate(self, context, bib_key):
        item = self.match_formalize(context, bib_key)
        if self.__add_info:
            item['info'] = Source.__format_info(self.__biblio[bib_key])
        return item

    def on_complete(self, context):
        # Because regex can match multiple keys, potentially, grab last one:
        key = self.__key_pattern.findall(context["base"])[-1]
        # Find the start of the key:
        key_offset = context["base"].rindex(key)
        # Search for the key in the biblio:
        key_regex = re.compile('^{}.*'.format(key).replace("@", ""))
        candidates = [
            self.__format_candidate(context, candidate) for candidate in list(
                filter(key_regex.match, self.__biblio.keys()))
        ]
        self.complete(context, context['startccol'] + key_offset, candidates)


source = Source(vim)

on_warmup = source.on_warmup
on_complete = source.on_complete
