from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from string import punctuation
import os



class Summarizer():

    def __init__(self):
        self.scored_words = {}
        self.scored_sentences = {}
        self.sentences = []
        self.words = []
        self.stop_words = stopwords.words("english") + list(punctuation)

    def process_text(self, file_name):
        with open(file_name, 'r') as f:
            lines = f.read().replace(os.linesep, " ")
            self.sentences = sent_tokenize(lines)
            self.words = [word for word in word_tokenize(lines) if word not in self.stop_words]

    def summarize(self, file_read, file_write, sentences=0):
        self.process_text(file_read)
        self.create_frequency_dict()

        if sentences == 0:
            sentences = int(len(self.sentences) * 6 / 10)
        elif sentences > len(self.sentences):
            sentences = len(self.sentences)

        temp_scored_sents = sorted(self.scored_sentences, reverse=True)
        output = []

        for score in temp_scored_sents[:sentences]:
            output.append(self.scored_sentences[score])

        with open(file_write, "w") as f:
            f.write(os.linesep.join([self.sentences[i] for i in sorted(output)]))

    def create_frequency_dict(self):
        self.scored_words = {}
        self.scored_sentences = {}

        for word in self.words:
            if word in self.scored_words:
                self.scored_words[word] += 1
            else:
                self.scored_words[word] = 1

        print(self.scored_words)

        for i, sentence in enumerate(self.sentences):
            self.scored_sentences[sum([self.scored_words[word] for word in word_tokenize(sentence) if word in self.words])] = i


summarizer = Summarizer()
summarizer.summarize("summaries/literature.txt", "summaries/literature-summary.txt")
summarizer.summarize("summaries/science.txt", "summaries/science-summary.txt")
summarizer.summarize("summaries/sports.txt", "summaries/sports-summary.txt")

