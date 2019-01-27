import nltk
from nltk.stem import PorterStemmer
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk import tag
from string import punctuation

import os
import operator
import re
import time


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

        for i in output:
            keyword_to_score = {}
            score_to_keyword = {}
            sentence = self.sentences[i]
            for word in word_tokenize(sentence):
                word = self.format_word(word)
                if word in self.scored_words:
                    keyword_to_score[word] = self.scored_words[word]
                    score_to_keyword[self.scored_words[word]] = word

            sentences = []

            for index in output:
                sentence = self.sentences[index]
                chunked_sentence = self.chunk_sentence(sentence)
                if chunked_sentence:
                    for chunk, pos_tag in chunked_sentence.items():
                        if pos_tag == "NM":
                            sentence = sentence.replace(chunk, "__" * len(chunk))
                sentences.append(sentence)

        with open(file_write, "w") as f:
            f.write(os.linesep.join([sentence for sentence in sentences]))

    def extract_keywords(self, file_read, file_write, keywords=0):
        self.process_text(file_read)
        self.create_words_frequency_dict()

        sorted_words = sorted(self.scored_words.items(), key=operator.itemgetter(1), reverse=True)

        if keywords == 0:
            keywords = len(sorted_words)

        with open(file_write, "w") as f:
            f.write(os.linesep.join([self.whole_words[stem] for stem, score in sorted_words[:keywords]]))

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

        grammar = """
            NM: {<NNP>{1,3}}
            NP: {<DT>*<JJ><NN.*>+}     #Chunk Noun Phrases
            VP: {<VB.*><NP>}           #Chunk Verb Phrases
            PR: {<IN><CD><TO><CD>}     #Chunk Periods(from...to...)           
        """
        cp = nltk.RegexpParser(grammar)
        parsed_sentence = cp.parse(tagged)

        results = {}

        for subtree in parsed_sentence.subtrees(filter=lambda t: t.label() in ["NP", "VP", "PR", "NM"]):
            items = []
            for item in subtree.leaves():
                items.append(item[0])

            results[" ".join(items)] = subtree.label()
        return False if not results else results


curr = time.time()
summarizer = Summarizer()

summarizer.summarize("summaries/history.txt", "summaries/history-summary.txt")
summarizer.summarize("summaries/literature.txt", "summaries/literature-summary.txt")
summarizer.summarize("summaries/science.txt", "summaries/science-summary.txt")
summarizer.summarize("summaries/sports.txt", "summaries/sports-summary.txt")

print(time.time() - curr)
