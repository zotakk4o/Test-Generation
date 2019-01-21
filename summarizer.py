from nltk.stem import PorterStemmer
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from string import punctuation
import os
import operator


class Summarizer:

    def __init__(self):
        self.ps = PorterStemmer()
        self.scored_words = {}
        self.scored_sentences = {}
        self.sentences = []
        self.stemmed_words = []
        self.whole_words = {}
        self.stop_words = stopwords.words("english") + list(punctuation) + ["'s", "'ve", "'ll", "'d", "'t", "'m", "“",
                                                                            "’", "”"]

    def process_text(self, file_name):
        with open(file_name, 'r') as f:
            lines = f.read().replace(os.linesep, " ")
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

        with open(file_write, "w") as f:
            f.write(os.linesep.join([self.sentences[i] for i in sorted(output)]))

    def extract_keywords(self, file_read, file_write, keywords=1):
        self.process_text(file_read)
        self.create_words_frequency_dict()

        sorted_words = sorted(self.scored_words.items(), key=operator.itemgetter(1), reverse=True)

        with open(file_write, "w") as f:
            f.write(", ".join([self.whole_words[stem] for stem, score in sorted_words[:keywords]]))

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
                 self.format_word(word) in self.stemmed_words])

        return sorted(self.scored_sentences.items(), key=operator.itemgetter(1), reverse=True)

    def format_word(self, word):
        return self.ps.stem(word.lower())


summarizer = Summarizer()
summarizer.summarize("summaries/literature.txt", "summaries/literature-summary.txt")
summarizer.summarize("summaries/science.txt", "summaries/science-summary.txt")
summarizer.summarize("summaries/sports.txt", "summaries/sports-summary.txt")

summarizer.extract_keywords("summaries/literature.txt", "summaries/literature-keywords.txt", 5)
summarizer.extract_keywords("summaries/science.txt", "summaries/science-keywords.txt", 5)
summarizer.extract_keywords("summaries/sports.txt", "summaries/sports-keywords.txt", 5)
