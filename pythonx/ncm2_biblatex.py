# -*- coding: utf-8 -*-

import os
import re
from glob import glob
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

        # Cache bibfile:
        self.__bibfiles = []
        self.__bib_files_mtimes = {}

        self.__pwd = self.vim.command_output(":pwd")

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
        self.source_bibs()

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

    def __source_bib(self, file):
        self.__bib_files.append(os.path.abspath(file))

    def __source_bibs(self, file):
        if self.__glob_re.search(file):
            for glob_file in glob(file):
                self.__source_bib(glob_file)
        else:
            self.__source_bib(file)

    def source_bibs(self):
        self.__bib_files = []
        files = self.__bib_file
        # Detect if the working directory has been changed by Vim:
        new_pwd = self.vim.command_output(":pwd")
        if self.__pwd != new_pwd:
            # If Vim is in a new working directory, change Python's PWD, too:
            os.chdir(new_pwd)
            self.__pwd = new_pwd
        if not isinstance(self.__bib_file, list):
            files = [self.__bib_file]
        for file in files:
            self.__source_bibs(file)
        for file in self.__bib_files:
            if not file in self.__bib_files_mtimes:
                self.__read_biblio()
            self.__bib_files_mtimes[file] = os.stat(file).st_mtime

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

source_bibs = source.source_bibs
on_warmup = source.on_warmup
on_complete = source.on_complete
