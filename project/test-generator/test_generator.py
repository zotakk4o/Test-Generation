import nltk
from nltk import tag
from nltk import word_tokenize
from utils.clean_utils import CleanUtils
from numpy import argsort
from collections import Counter

import json
import os
import re
import networkx as nx
import itertools
import operator


class TestGenerator:

    def __init__(self, text, percentage=50):
        self.results = self.prepare_test_sentences(text, percentage)
        self.sentences = []

    @staticmethod
    def is_there_tag(sentence, search):
        items = tag.pos_tag(word_tokenize(sentence))
        items = [val for key, val in items]
        for item in items:
            if search in item:
                return True
        return False

    @staticmethod
    def build_graph(nodes):
        gr = nx.Graph()
        gr.add_nodes_from(nodes)
        node_pairs = list(itertools.combinations(nodes, 2))

        for pair in node_pairs:
            first_string = pair[0]
            second_string = pair[1]
            lev_distance = nltk.edit_distance(first_string, second_string)
            gr.add_edge(first_string, second_string, weight=lev_distance)

        return gr

    def extract_sentences(self, text):
        sentence_tokens = CleanUtils.clean_text(text)
        self.sentences = [re.sub("[(\[{][^)}\]]*[)\]}]", "", sent.replace(os.linesep, " ")) for sent in
                          CleanUtils.tokenize_sentences(text)]
        graph = self.build_graph(sentence_tokens)

        calculated_page_rank = nx.pagerank(graph, weight='weight')
        indices = argsort(list(calculated_page_rank.values()))[::-1]

        ranked_sentences = [x for _, x in sorted(zip(indices, self.sentences))]

        return ranked_sentences

    def extract_gaps(self):

        def order_gaps(haystack, chunks, delimiter):
            chunks = list(filter(None, chunks.split(delimiter)))
            indexed = {}
            for gap in chunks:
                indexed[haystack.index(gap)] = gap

            indexed = sorted(indexed.items(), key=operator.itemgetter(0))
            return [gap for i, gap in indexed]

        gaps = []
        for sentence, chunked_sentence in self.results:
            original_sentence = sentence
            candidates_removed = 0
            chunks_removed = ""
            lnms_removed = 0
            chunks_removed_delimiter = "~$~$~"

            print(Counter(chunked_sentence.values()))

            if "NB" not in chunked_sentence.values():
                pos_tags_counter = Counter(chunked_sentence.values())
                for chunk_name in ["LNM", "NM"]:
                    for index, (chunk, pos_tag) in enumerate(chunked_sentence.items()):
                        if pos_tag == chunk_name and chunk not in chunks_removed and candidates_removed <= 1:

                            if lnms_removed != 0 and pos_tags_counter["LNM"] > 1 and pos_tag == "LNM":
                                continue
                            elif pos_tag == "LNM":
                                lnms_removed += 1

                            chunk = chunk.replace(" ,", ",")
                            sentence = sentence.replace(chunk, "_" * len(chunk))
                            candidates_removed += 1
                            chunks_removed += chunk + chunks_removed_delimiter

                if len(chunks_removed):
                    chunks_removed = order_gaps(original_sentence, chunks_removed, chunks_removed_delimiter)
                    gaps.append((sentence, chunks_removed))

        return gaps

    def extract_bonuses(self):
        bonuses = []
        for sentence, chunked_sentence in self.sentences:
            dsc_phrases = self.extract_description_phrases(chunked_sentence)
            if dsc_phrases:
                for object_of_description, phrase in dsc_phrases:
                    if len(phrase.strip().split(" ")) > 2:
                        bonuses.append((object_of_description, phrase))

        return bonuses

    def extract_sentence_completion(self):
        questions = []

        for sentence, chunked_sentence in self.sentences:
            """TODO"""

        return questions

    def prepare_test_sentences(self, text, percentage):
        summary_sentences = self.extract_sentences(text)
        test_size = int(len(summary_sentences) * percentage / 100)
        indexes = [self.sentences.index(sent) for sent in summary_sentences[:test_size]]
        test_sentences = [self.sentences[index] for index in indexes]

        results = []

        for sentence in test_sentences:
            chunked_sentence = self.chunk_sentence(sentence)
            if chunked_sentence:
                results.append((sentence, chunked_sentence))

        return results

    def chunk_sentence(self, sentence):
        sentence = word_tokenize(sentence)
        tagged = tag.pos_tag(sentence)

        grammar = {
            "NBS": "{<IN><CD>}",
            "NM": "{<DT>*<JJ.*>*<NNP.*>+(<IN><DT>*<JJ.*>*<NNP.*>+)*}",
            "NB": "{(<NBS><TO|CC|NM|IN><CD|NM>*)"
                  "|((<IN><NM|,>+|<NM>)<CD><,>*<CD>*)}",
            "LNM": "{<NM>(<,>*<CC><NM>|<,><CC>*<NM>)}",
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
        chunks = []
        for chunk, pos_tag in chunked_sentence.items():
            if pos_tag == "DSCS":
                tagged_chunk = self.chunk_sentence(chunk)
                if tagged_chunk:
                    description_chunks = [key for key, value in tagged_chunk.items() if
                                          value in ["DSC", "DSCS"]]
                    if description_chunks:
                        for object_of_description, description in self.extract_descriptions(description_chunks):
                            chunks.append((object_of_description, description))

        return chunks

    def extract_descriptions(self, description_chunks):
        descriptions = []
        object_of_description = description_chunks[0]
        delimiter = "$$$$"
        for index in range(1, len(description_chunks)):
            desc = description_chunks[index]
            if re.search("\s(is|are|was|were)", desc):
                object_of_description = object_of_description.replace(desc, delimiter)

        for description in object_of_description.split(delimiter)[1:]:
            description = description.split('.')[0].strip()
            if not self.is_there_tag(description, "PRP"):
                descriptions.append(description)

        return object_of_description, descriptions



#print(generator.extract_gaps())
