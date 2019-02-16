import nltk
from nltk.stem import PorterStemmer
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk import tag
from string import punctuation

import json
import os
import operator
import re


class Summarizer:

    def __init__(self):
        self.ps = PorterStemmer()
        self.scored_words = {}
        self.scored_sentences = {}
        self.sentences = []
        self.stemmed_words = []
        self.whole_words = {}
        self.stop_words = stopwords.words("english") + list(punctuation) + ["'s", "'ve", "'ll", "'d", "'t", "'m", "“",
                                                                            "’", "”", ";", "“"]
        self.prioritized_tags = ["LNM", "NB", "NM", "NP"]

    def process_text(self, file_name):
        with open(file_name, 'r') as f:
            lines = re.sub("\([^)]*\)", "", f.read().replace(os.linesep, " "))
            self.sentences = sent_tokenize(lines)
            self.stemmed_words = []
            self.whole_words = {}

            for word in word_tokenize(lines):
                if word.lower() not in self.stop_words:
                    stem = self.format_word(word)
                    self.stemmed_words.append(stem)
                    self.whole_words[stem] = word

    def summarize(self, file_read, file_write, percentage=60):
        self.process_text(file_read)

        output = []
        length_of_summary = int(len(self.sentences) * percentage / 100)

        for index, score in self.create_sentences_frequency_dict()[:length_of_summary]:
            output.append(index)

        output = sorted(output)
        sentences = []
        chunks = []

        for i in output:
            keyword_to_score = {}
            score_to_keyword = {}
            sentence = self.sentences[i]
            for word in word_tokenize(sentence):
                word = self.format_word(word)
                if word in self.scored_words:
                    keyword_to_score[word] = self.scored_words[word]
                    score_to_keyword[self.scored_words[word]] = word

            chunked_sentence = self.chunk_sentence(sentence)
            if chunked_sentence:
                for chunk, pos_tag in chunked_sentence.items():
                    if pos_tag == "DSCS":
                        chunked_chunk = self.chunk_sentence(chunk)
                        if chunked_chunk:
                            dsc = [key for key, value in chunked_chunk.items() if value == "DSC"]
                            if dsc:
                                if re.search("\s(is|are|was|were)", dsc[0]):
                                    chunks.append(chunk)

                with open(file_write.replace("summary", "bonus"), "w") as f:
                    f.write(os.linesep.join(chunks))

                chunks_removed = []
                for chunk_name in self.prioritized_tags:
                    
                    for chunk, pos_tag in chunked_sentence.items():
                        if pos_tag == chunk_name and chunk not in chunks_removed and len(chunks_removed) <= 1:
                            sentence = sentence.replace(chunk, "_" * len(chunk))
                            chunks_removed.append(chunk)
                sentence = sentence + "GAPS => " + json.dumps(chunks_removed)

            sentences.append(sentence)

        with open(file_write, "w") as f:
            f.write(os.linesep.join([sentence for sentence in sentences]))

    def create_words_frequency_dict(self):
        self.scored_words = {}

        for word in self.stemmed_words:
            if word in self.scored_words:
                self.scored_words[word] += 1
            else:
                self.scored_words[word] = 1

    def create_sentences_frequency_dict(self):
        self.scored_sentences = {}
        self.create_words_frequency_dict()

        for i, sentence in enumerate(self.sentences):
            self.scored_sentences[i] = sum(
                [self.scored_words[self.format_word(word)] for word in word_tokenize(sentence) if
                 self.format_word(word) in self.stemmed_words]) / 1000

        return sorted(self.scored_sentences.items(), key=operator.itemgetter(1), reverse=True)

    def format_word(self, word):
        return self.ps.stem(word.lower())

    def chunk_sentence(self, sentence):
        sentence = word_tokenize(sentence)
        tagged = tag.pos_tag(sentence)

        grammar = {
            "NM": "{<DT>*<NNP>{1,4}}",
            "LNM": "{<NM>(<,>*<CC><NM>|<,><CC>*<NM>)+}",
            "NP": "{<DT>*<RB.*|JJ.*>+<NN.*>+}",  # NP: <DT>*<JJ.*><NN.*>
            "NB": "{<IN><CD><TO|CC|NM>*<CD>*<NM>*}",
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


summarizer = Summarizer()

summarizer.summarize("summarizer/summaries/history.txt", "summarizer/summaries/history-summary.txt", 100)
summarizer.summarize("summarizer/summaries/literature.txt", "summarizer/summaries/literature-summary.txt", 100)
summarizer.summarize("summarizer/summaries/science.txt", "summarizer/summaries/science-summary.txt", 100)
summarizer.summarize("summarizer/summaries/sports.txt", "summarizer/summaries/sports-summary.txt", 100)
