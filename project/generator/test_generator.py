import nltk
from nltk import tag
from nltk import word_tokenize, sent_tokenize
from project.generator.utils.clean_utils import CleanUtils
from numpy import argsort
from collections import Counter
from random import choice

import json
import os
import re
import networkx as nx
import itertools
import operator


class TestGenerator:

    def __init__(self, text, percentage=50):
        self.sentences = []
        self.results = self.prepare_test_sentences(text, percentage)

    @staticmethod
    def is_there_tag(sentence, search):
        """
        Looks for a given part of speach tag in a sentence

        :param sentence: the sentence to search
        :param search: the pos tag to search for
        :return: True/False
        """
        items = tag.pos_tag(word_tokenize(sentence))
        items = [val for key, val in items]
        for item in items:
            if search in item:
                return True
        return False

    @staticmethod
    def build_graph(nodes):
        """
        Constructs a graph with nodes the sentences and edge weights the Levenshtein distance of two sentences
        :param nodes: array of clean sentences
        :return: graph for Textrank
        """
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
        """
        Ranks the input text sentences by the Textrank algorithm

        :param text: the text to rank by Textrank
        :return: array of ranked sentences in descending order of importance
        """
        sentence_tokens = CleanUtils.clean_text(text)
        self.sentences = [re.sub("[(\[{][^)}\]]*[)\]}]", "", sent.replace(os.linesep, " ")) for sent in
                          CleanUtils.tokenize_sentences(text)]
        graph = self.build_graph(sentence_tokens)

        calculated_page_rank = nx.pagerank(graph, weight='weight')
        indices = argsort(list(calculated_page_rank.values()))

        ranked_sentences = [x for _, x in sorted(zip(indices, self.sentences))]

        return ranked_sentences

    def order_gaps(self, haystack, chunks, delimiter):
        """
        Helper function to retrieve position of description and the description itself

        :param haystack: a sentence with description
        :param chunks: list of descriptions
        :param delimiter: delimiter used to mark the descriptions
        :return:
        """
        chunks = list(filter(None, chunks.split(delimiter)))
        indexed = {}
        for gap in chunks:
            if gap in haystack:
                indexed[haystack.index(gap)] = gap

        indexed = sorted(indexed.items(), key=operator.itemgetter(0))
        return [gap for i, gap in indexed]

    def extract_gaps(self, gaps_only=True):
        """
        Extracts important information, leaving gaps in their place

        :param gaps_only: whether the sentences are going to be processed for sentence_completion or not
        :return: (question, answer) pairs
        """

        gaps = []
        for sentence, chunked_sentence in self.results:
            original_sentence = sentence
            candidates_removed = 0
            chunks_removed = ""
            lnms_removed = 0
            chunks_removed_delimiter = "~$~$~"

            if not gaps_only and "NB" in chunked_sentence.values():
                continue

            pos_tags_counter = Counter(chunked_sentence.values())
            for chunk_name in ["LNM", "NM"]:  # prioritize List of Names over Names
                for chunk, pos_tag in chunked_sentence.items():
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
                chunks_removed = self.order_gaps(original_sentence, chunks_removed, chunks_removed_delimiter)
                gaps.append((sentence, chunks_removed))

        return gaps

    def extract_bonuses(self):
        """
        Extracts bonus questions from a sentence. A bonus question is a sentence with a description phrase "Steve is pretty" -> "_ pretty"

        :return: bonuse questions
        """
        bonuses = []
        for sentence, chunked_sentence in self.results:
            dsc_phrases = self.extract_description_phrases(chunked_sentence)
            if dsc_phrases:
                for object_of_description, phrase in dsc_phrases:
                    if len(phrase.strip().split(" ")) > 2:
                        bonuses.append((object_of_description, "_" * len(object_of_description) + phrase))

        return bonuses

    def extract_sentence_completion(self, completion_only=True):
        """
        Extracts the important information from a sentence for sentence completion - 4 possible answers
        :param completion_only: whether the sentences are going to be processed for fill in the gaps questions
        :return: (question, answer) pairs
        """
        questions = []

        for sentence, chunked_sentence in self.results:
            candidates_removed = 0

            for chunk_name in ["NB", "NBS"]:  # prioritize Periods over Single Numbers
                if not completion_only and chunk_name == "NBS" and ("NM" or "LNM") in chunked_sentence.values():
                    break
                if candidates_removed == 0:
                    for chunk, pos_tag in chunked_sentence.items():
                        if pos_tag == chunk_name:
                            answers = set()
                            chunk = chunk.replace(" ,", ",")

                            if chunk[-1] == ',':
                                chunk = chunk[:-1]

                            gaped_sentence = sentence.replace(chunk, "_" * len(chunk))
                            chunk = CleanUtils.clean_commas(chunk)
                            answers.add(chunk)
                            while len(answers) < 4:
                                candidate = self.replace_numbers(list(answers)[-1])
                                if candidate:
                                    answers.add(candidate)
                                else:
                                    break
                            if len(answers) == 4:
                                questions.append((gaped_sentence, list(answers), chunk))
                                candidates_removed = 1
                                break

        return questions

    def prepare_test_sentences(self, text, percentage):
        """
        Starts the whole algorithm for test generation

        :param text: text to process
        :param percentage: what part of the ranked sentences to take for the test
        :return: test sentences
        """
        summary_sentences = self.extract_sentences(text)
        test_size = int(len(summary_sentences) * percentage / 100)
        indexes = [self.sentences.index(sent) for sent in summary_sentences[:test_size]]
        indexes = sorted(indexes)
        test_sentences = [self.sentences[index] for index in indexes]

        results = []

        for sentence in test_sentences:
            chunked_sentence = self.chunk_sentence(sentence)
            if chunked_sentence:
                results.append((sentence, chunked_sentence))

        return results

    def chunk_sentence(self, sentence):
        """
        Converts sentences into words and tags the words with their corresponding POS tag

        :param sentence: the sentence to process
        :return: the tagged sentence words or False if none
        """
        sentence = word_tokenize(sentence)
        tagged = tag.pos_tag(sentence)

        grammar = {
            "NBS": "{<IN><DT|JJ.*>*<CD>}",
            "NM": "{<DT>*<JJ.*>*<NNP.*>+(<IN><DT>*<JJ.*>*<NNP.*>+)*}",
            "NB": "{(<NBS><TO|CC|NM|IN|JJ.*>+<CD>*)"
                  "|((<IN><NM|,>+|<NM>)<CD><,>*<CD>*)}",
            "LNM": "{<NM>(<,>*<CC><NM>|<,><CC>*<NM>)}",
            "DSC": "{<NM><VB.*>}",
            "DSCS": "{<DSC><.*>+}"
        }
        grammar_string = re.sub(r"(?<=}),", os.linesep, json.dumps(grammar)[1:-1].replace("\"", ""))

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
        """
        Extracts descriptions -> Steve is pretty -> (Steve is, pretty)
        :param chunked_sentence: the POS tagged sentence
        :return: (object of description, description) pairs
        """
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
        """
        Helper function used to extract descriptions and objects of the description

        :param description_chunks:
        :return: all descriptions and their corresponding objects in a sentence
        """
        objects_of_description = []
        descriptions = []
        sentence = description_chunks[0]
        delimiter = "~$~$~"

        for index in range(1, len(description_chunks)):
            desc = description_chunks[index]
            if re.search(r"\s(is|are|was|were)", desc):
                sentence = sentence.replace(desc, delimiter)
                objects_of_description.append(desc)

        for description in sentence.split(delimiter)[1:]:
            description = sent_tokenize(description.strip())[0]
            if not self.is_there_tag(description, "PRP"):
                descriptions.append(description)

        return zip(objects_of_description, descriptions)

    @staticmethod
    def replace_numbers(num):
        """
        Generates random valid dates/ranges for sentence completion that are close to the answer

        :param num: the date/range to tweak
        :return: changed version of the num
        """
        is_changed = False
        num = CleanUtils.clean_commas(num)

        months = ['January', 'February', 'March', 'April',
                  'May', 'June', 'July', 'August',
                  'September', 'October', 'November', 'December']
        weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for day in weekdays:
            if day in num:
                weekdays.remove(day)
                num = num.replace(day, choice(weekdays))
                is_changed = True
        for month in months:
            if month in num:
                months.remove(month)
                num = num.replace(month, choice(months))
                is_changed = True

        if re.findall(r'(?<!\d)(\d+)(?!\d)', num):
            change = choice(list(range(-10, -1)) + list(range(1, 10)))
            padding = 0
            for number in re.finditer(r'(?<!\d])(\d+)(?!\d)', num):
                old_n = number.group().strip()
                new_n = int(old_n)
                if 0 < new_n <= 31:
                    change_date = list(range(1, 29))
                    if new_n < 29:
                        change_date.remove(new_n)
                    new_n = choice(change_date)
                else:
                    new_n += change
                num = (num[:number.start() + padding] + f"{str(new_n)}" + num[number.end() + padding:]).replace(" ,",
                                                                                                                ",").strip()
                padding = len(str(new_n)) - len(str(old_n))
                is_changed = True

        return num if is_changed else False
