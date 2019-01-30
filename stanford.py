import os
from nltk.parse import stanford
from nltk import pos_tag
from nltk.corpus import stopwords

import itertools
import editdistance
import networkx as nx
from clean_utils import *
from numpy import argsort


def build_graph(nodes):

    gr = nx.Graph()  # initialize the graph
    gr.add_nodes_from(nodes)
    nodePairs = list(itertools.combinations(nodes, 2))

    for pair in nodePairs:
        firstString = pair[0]
        secondString = pair[1]
        levDistance = editdistance.eval(firstString, secondString)
        gr.add_edge(firstString, secondString, weight=levDistance)

    return gr

def extract_sentences(filename):

    sentence_tokens = clean_file(filename)
    original_sentences = tokenize_sentences(read_file(filename))
    graph = build_graph(sentence_tokens)

    calculated_page_rank = nx.pagerank(graph, weight='weight')
    # print(calculated_page_rank)

    indices = argsort(list(calculated_page_rank.values()))[::-1]
    indices = indices[0: len(indices)//3 + 1]

    ranked_sentences = {i:x for i, x in sorted(zip(indices, original_sentences))}

    return ranked_sentences

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

def filter_for_tags(tagged, tags=['NN', 'JJ', 'NNP', 'CD']):  # try with other tags as well (verbs?)
    return [item for item in tagged if item[1] in tags]

def extract_key_phrases(filename):

    word_tokens = clean_file(filename, to_words=True, stem=False, stop=False)

    # assign POS tags to the words in the text
    tagged = pos_tag(word_tokens)
    textlist = [x[0] for x in tagged]

    tagged = filter_for_tags(tagged)

    unique_word_set = unique_element([x[0] for x in tagged])
    word_set_list = list(unique_word_set)
    word_set_list = stem_words(word_set_list)

    graph = build_graph(word_set_list)

    calculated_page_rank = nx.pagerank(graph, weight='weight', alpha=0.7)

    # keywords = sorted(calculated_page_rank, key=calculated_page_rank.get, reverse=True)
    return calculated_page_rank


class GapSelection:

    def __init__(self):
        os.environ["CLASSPATH"] = "C:\\Users\\Bobbie the gamer\\Desktop\\stanford-parser-full-2018-10-17\\stanford-parser-full-2018-10-17"
        os.environ['STANFORD_MODELS'] = "C:\\Users\\Bobbie the gamer\\Desktop\\stanford-parser-full-2018-10-17\\stanford-parser-full-2018-10-17"
        os.environ['JAVAHOME'] = "C:\\Program Files\\Java\\jdk1.8.0_171\\bin"

    def _prepare_parser(self):
        """Prepare stanford parser
        - Args:
        - Returns:
            parser: stanfrod parser
        """
        parser = stanford.StanfordParser()
        return parser

    def _parse(self, sentence):
        parser = self._prepare_parser()
        parsed_sentence = list(parser.raw_parse((sentence)))
        return parsed_sentence

    def _extract_gaps(self, sentence, tree):
        candidates = []
        candidate = {}
        entities = ['NP', 'ADJP', 'NNP', 'CD']
        entities = list(map(lambda x: list(x.subtrees(
            filter=lambda x: x.label() in entities)), tree))[0]
        # if len(entities) > 7:
        #     print("here0")
        #     return False
        # else:
        for entity in entities:
            candidate_gap = str(' '.join(entity.leaves()))
            sentence_copy = sentence
            # replace sentence candidate_gap with ___
            sentence_copy = sentence_copy.replace(candidate_gap, '_____')
            candidate['Sentence'] = sentence
            candidate['Question'] = sentence_copy
            candidate['Answer'] = candidate_gap
            if candidate_gap.strip() != sentence.strip():
                candidates.append(candidate)
            candidate = {}
        return candidates

    def get_candidates(self, sentences):
        candidates = []
        for sentence_id, sentence in sentences.items():
            # print(sen tence_id)
            tree = self._parse(sentence)
            current_sentence_candidates = self._extract_gaps(
                sentence, tree)  # build candidate questions
            if current_sentence_candidates == False:
                continue

            candidates = candidates + current_sentence_candidates
            print("building candidate question/answer pairs", len(candidates))
            # clear current_sentence_candidates
            current_sentence_candidates = []
        return candidates

    def select_candidates(self, keywords, candidates, sentences):
        best_gaps = {}
        ss = set([d["Question"] for d in candidates])
        for i, s in sentences.items():
            gaps = [d["Answer"] for d in list(filter(lambda x: x["Sentence"] == s, candidates))]
            questions = [d["Question"] for d in list(filter(lambda x: x["Sentence"] == s, candidates))]
            score = [0]*len(gaps)
            for n, gap in enumerate(gaps):
                gs = gap.split()
                stopWords = set(stopwords.words('english'))
                gs2 = [g for g in gs if g not in stopWords]
                for g in gs2:  # used for including phrases into the gap list
                    for word, pg_score in keywords.items():
                        score[n] += (editdistance.eval(g, word))/pg_score
                o = 1/len(gs2) if len(gs2) is not 0 else 0
                score[n] *= o

            best_gaps[questions[score.index(min(score))]] = gaps[score.index(min(score))]
        
        return best_gaps

test = GapSelection()

text = "results/s2.txt"
sentences = extract_sentences(text)
phrases = extract_key_phrases(text)
selection = test.select_candidates(phrases, test.get_candidates(sentences), sentences)
with open(text.split(".")[0] + "_gaps.txt", 'w') as f:
    for k, v in selection.items():
        f.write(k + " -- " + v + "\n")

text = "results/t2.txt"
sentences = extract_sentences(text)
phrases = extract_key_phrases(text)
selection = test.select_candidates(phrases, test.get_candidates(sentences), sentences)
with open(text.split(".")[0] + "_gaps.txt", 'w') as f:
    for k, v in selection.items():
        f.write(k + " -- " + v + "\n")