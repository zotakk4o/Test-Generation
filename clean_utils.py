import string
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk import word_tokenize, sent_tokenize


def read_file(filepath):
    with open(filepath, 'r', encoding='utf8') as file:
        return file.read().replace("\n", " ").replace("\r", " ")

def remove_stopwords(text):
    stop = stopwords.words('english')
    return ' '.join([word for word in text.split() if word not in stop])

def tokenize_sentences(text):
    return sent_tokenize(text)

def tokenize_words(text):
    return word_tokenize(text)

def stem_words(words):
    stemmer = PorterStemmer()
    return [stemmer.stem(word) for word in words]

def remove_punctuation(text):
    punc = string.punctuation
    return text.translate(str.maketrans('', '', punc))

def clean_file(filepath, to_words=False, stem=True):
    text = read_file(filepath)
    text = text.lower()
    text = remove_stopwords(text)

    if to_words:
        text = remove_punctuation(text)
        tokens = tokenize_words(text)
        if stem:
            tokens = stem_words(tokens)
    else:
        tokens = tokenize_sentences(text)
        tokens = [remove_punctuation(token) for token in tokens]
        if stem:
            tokens = [" ".join(stem_words(t.split())) for t in tokens]        

    return tokens
