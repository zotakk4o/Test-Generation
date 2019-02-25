import string
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk import word_tokenize, sent_tokenize


class CleanUtils:

    @staticmethod
    def remove_stopwords(text):
        stop = stopwords.words('english')
        return ' '.join([word for word in text.split() if word not in stop])

    @staticmethod
    def tokenize_sentences(text):
        return sent_tokenize(text)

    @staticmethod
    def tokenize_words(text):
        return word_tokenize(text)

    @staticmethod
    def stem_words(words):
        stemmer = PorterStemmer()
        return [stemmer.stem(word) for word in words]

    @staticmethod
    def remove_punctuation(text):
        punc = string.punctuation
        return text.translate(str.maketrans('', '', punc))

    @staticmethod
    def clean_file(text, to_words=False, stem=True):
        text = text.lower()
        text = CleanUtils.remove_stopwords(text)

        if to_words:
            text = CleanUtils.remove_punctuation(text)
            tokens = CleanUtils.tokenize_words(text)
            if stem:
                tokens = CleanUtils.stem_words(tokens)
        else:
            tokens = CleanUtils.tokenize_sentences(text)
            tokens = [CleanUtils.remove_punctuation(token) for token in tokens]
            if stem:
                tokens = [" ".join(CleanUtils.stem_words(t.split())) for t in tokens]

        return tokens
