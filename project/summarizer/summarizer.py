import nltk
from nltk.stem import PorterStemmer
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk import tag
from string import punctuation

import json
import os
import re


class Summarizer:

    def __init__(self):
        self.ps = PorterStemmer()
        self.scored_words = {}
        self.scored_sentences = {}
        self.sentences = []
        self.stop_words = stopwords.words("english") + list(punctuation) + ["'s", "'ve", "'ll", "'d", "'t", "'m", "“",
                                                                            "’", "”", ";", "“"]

    def summarize(self, text, percentage=60):
        output = []
        length_of_summary = int(len(self.sentences) * percentage / 100)

        sentences = []
        chunks = []
        nbs = []

        for i in output:
            chunked_sentence = self.chunk_sentence(sentence)
            if chunked_sentence:
                chunks_removed = []
                dsc_phrases = self.extract_description_phrases(chunked_sentence)
                if dsc_phrases:
                    for phrase in dsc_phrases:
                        if len(phrase.strip().split(" ")) > 2:
                            chunks.append(phrase)

                for chunk, pos_tag in chunked_sentence.items():
                    if pos_tag == "NB" and re.search("[0-9]+", chunk):
                        nbs.append(chunk)

                for chunk_name in self.prioritized_tags:
                    for chunk, pos_tag in chunked_sentence.items():
                        if pos_tag == chunk_name and chunk not in chunks_removed and len(chunks_removed) <= 1:
                            sentence = sentence.replace(chunk, "_" * len(chunk))
                            chunks_removed.append(chunk)
                sentence = sentence
            sentences.append(sentence)

    def chunk_sentence(self, sentence):
        sentence = word_tokenize(sentence)
        tagged = tag.pos_tag(sentence)

        grammar = {
            "NM": "{<DT>*<NNP>{1,4}}",
            "NP": "{<DT>*<RB.*|JJ.*>+<NN.*>+}",
            "NB": "{(<IN><CD><TO|CC|NM|IN>*<CD>*<NM>*)"
                  "|((<IN><NM|,>+|<NM>)<CD><,>*<CD>*)}",
            "LNM": "{<NM>(<.>*<CC><NM>|<.><CC>*<NM>)+}",
            "DSC": "{<NM><VB.*>}",
            "DSCS": "{<DSC><.*>+}"
        }
        grammar_string = re.sub("(?<=}),", os.linesep, json.dumps(grammar)[1:-1].replace("\"", ""))

        cp = nltk.RegexpParser(grammar_string)
        parsed_sentence = cp.parse(tagged)
        results = {}

        for subtree in parsed_sentence.subtrees(filter=lambda t: t.label() in grammar.keys()):
            items = []
            for item in subtree.leaves():
                items.append(item[0])

            results[" ".join(items)] = subtree.label()
        return False if not results else results

    def extract_description_phrases(self, chunked_sentence):
        chunks = set()
        for chunk, pos_tag in chunked_sentence.items():
            if pos_tag == "DSCS":
                tagged_chunk = self.chunk_sentence(chunk)
                if tagged_chunk:
                    description_chunks = [key for key, value in tagged_chunk.items() if
                                          value in ["DSC", "DSCS"]]
                    if description_chunks:
                        for description in self.extract_descriptions(description_chunks):
                            chunks.add(description)

        return chunks

    def extract_descriptions(self, description_chunks):
        descriptions = []
        sent = description_chunks[0]
        delimiter = "$$$$"
        for index in range(1, len(description_chunks)):
            desc = description_chunks[index]
            if re.search("\s(is|are|was|were)", desc):
                sent = sent.replace(desc, delimiter)

        for description in sent.split(delimiter)[1:]:
            description = description.split('.')[0].strip()
            if not self.is_there_tag(description, "PRP"):
                descriptions.append(description)

        return descriptions

    def is_there_tag(self, sentence, search):
        items = tag.pos_tag(word_tokenize(sentence))
        items = [val for key, val in items]
        for item in items:
            if search in item:
                return True
        return False
