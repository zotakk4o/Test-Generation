import io
import os
import nltk
import itertools
import editdistance
import networkx as nx

from numpy import argsort

from clean_utils import *
import matplotlib.pyplot as plt


def build_graph(nodes):

    gr = nx.Graph()  # initialize the graph
    gr.add_nodes_from(nodes)
    nodePairs = list(itertools.combinations(nodes, 2))

    for pair in nodePairs:
        firstString = pair[0]
        secondString = pair[1]
        levDistance = editdistance.eval(firstString, secondString)
        gr.add_edge(firstString, secondString, weight=levDistance)

    # nx.draw(gr, with_labels=True)
    # plt.show()

    return gr

def extract_sentences(filename):

    sentence_tokens = clean_file(filename)
    original_sentences = tokenize_sentences(read_file(filename))
    graph = build_graph(sentence_tokens)

    calculated_page_rank = nx.pagerank(graph, weight='weight')
    indices = argsort(list(calculated_page_rank.values()))[::-1]

    ranked_sentences = [x for _, x in sorted(zip(indices, original_sentences))] 
    summary = "\n".join(str(i+1) + "--" + x for i, x in enumerate(ranked_sentences))

    with open(filename.split(".")[0] + "_result.txt", "w") as f:
        f.write(summary)

def unique_element(iterable, key=None):
    seen = set()
    if key is None:
        for element in [x for x in iterable if x not in seen]:
            seen.add(element)
            yield element
    else:
        for element in iterable:
            k = key(element)
            if k not in seen:
                seen.add(k)
                yield element

def filter_for_tags(tagged, tags=['NN', 'JJ', 'NNP']):  # try with other tags as well (verbs?)
    return [item for item in tagged if item[1] in tags]

def extract_key_phrases(filename):

    word_tokens = clean_file(filename, to_words=True, stem=False)

    # assign POS tags to the words in the text
    tagged = nltk.pos_tag(word_tokens)
    textlist = [x[0] for x in tagged]

    tagged = filter_for_tags(tagged)

    unique_word_set = unique_element([x[0] for x in tagged])
    word_set_list = list(unique_word_set)
    word_set_list = stem_words(word_set_list)

    graph = build_graph(word_set_list)

    calculated_page_rank = nx.pagerank(graph, weight='weight')

    keyphrases = sorted(calculated_page_rank, key=calculated_page_rank.get, reverse=True)

    # reduce count to one third
    keyphrases = keyphrases[0:len(word_set_list)//3 + 1]

    modified_key_phrases = set([])
    dealt_with = set([])
    i = 0
    j = 1
    while j < len(textlist):
        first = textlist[i]
        second = textlist[j]
        if first in keyphrases and second in keyphrases:
            keyphrase = first + ' ' + second
            modified_key_phrases.add(keyphrase)
            dealt_with.add(first)
            dealt_with.add(second)
        else:
            if first in keyphrases and first not in dealt_with:
                modified_key_phrases.add(first)

            if j == len(textlist) - 1 and second in keyphrases and \
                    second not in dealt_with:
                modified_key_phrases.add(second)

        i = i + 1
        j = j + 1

    with open(filename.split(".")[0] + "_result_keyphrases.txt", "w") as f:
        f.write(",\n".join(modified_key_phrases))

extract_key_phrases("sport.txt")
extract_sentences("sport.txt")
extract_key_phrases("literature.txt")
extract_sentences("literature.txt")
extract_key_phrases("science.txt")
extract_sentences("science.txt")
