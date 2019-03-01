import nltk
from nltk import tag
from nltk import word_tokenize
from clean_utils import CleanUtils
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
        gr = nx.Graph()  # initiate the graph
        gr.add_nodes_from(nodes)  # add the sentences as nodes
        node_pairs = list(itertools.combinations(nodes, 2))  # pair up nodes to prepare for edge createion

        for pair in node_pairs:
            first_string = pair[0]
            second_string = pair[1]
            lev_distance = nltk.edit_distance(first_string, second_string)  # calculate the Levenshtein distance between the nodes
            gr.add_edge(first_string, second_string, weight=lev_distance)  # add the distance as the edge between nodes

        return gr

    def extract_sentences(self, text):
        sentence_tokens = CleanUtils.clean_text(text)  # clean text up
        self.sentences = [re.sub("[(\[{][^)}\]]*[)\]}]", "", sent.replace(os.linesep, " ")) for sent in
                          CleanUtils.tokenize_sentences(text)]
        graph = self.build_graph(sentence_tokens)  # build the graph

        calculated_page_rank = nx.pagerank(graph, weight='weight')  # calculate the PageRank score of each sentence
        indices = argsort(list(calculated_page_rank.values()))[::-1]  # sort the sentences accordingly

        ranked_sentences = [x for _, x in sorted(zip(indices, self.sentences))]  # uncleaned sentences sorted accoording to PageRank score

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
            "NM": "{<DT>*<JJ.*>*<NNP.*>+(<IN><DT>*<JJ.*>*<NNP.*>+)*}",
            "NB": "{(<IN><CD><TO|CC|NM|IN><CD|NM>*)"
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


generator = TestGenerator("""
World War I (often abbreviated as WWI or WW1), also known as the First World War or the Great War, was a global war originating in Europe that lasted from 28 July 1914 to 11 November 1918. Contemporaneously described as "the war to end all wars",[7] it led to the mobilisation of more than 70 million military personnel, including 60 million Europeans, making it one of the largest wars in history.[8][9] It is also one of the deadliest conflicts in history,[10] with an estimated nine million combatants and seven million civilian deaths as a direct result of the war, while resulting genocides and the 1918 influenza pandemic caused another 50 to 100 million deaths worldwide.[11]

On 28 June 1914, Gavrilo Princip, a Bosnian Serb Yugoslav nationalist, assassinated the Austro-Hungarian heir Archduke Franz Ferdinand in Sarajevo, leading to the July Crisis.[12][13] In response, on 23 July Austria-Hungary issued an ultimatum to Serbia. Serbia's reply failed to satisfy the Austrians, and the two moved to a war footing.

A network of interlocking alliances enlarged the crisis from a bilateral issue in the Balkans to one involving most of Europe. By July 1914, the great powers of Europe were divided into two coalitions: the Triple Entente—consisting of France, Russia and Britain—and the Triple Alliance of Germany, Austria-Hungary and Italy (the Triple Alliance was primarily defensive in nature, allowing Italy to stay out of the war in 1914).[14] Russia felt it necessary to back Serbia and, after Austria-Hungary shelled the Serbian capital of Belgrade on the 28th, partial mobilisation was approved.[15] General Russian mobilisation was announced on the evening of 30 July; on the 31st, Austria-Hungary and Germany did the same, while Germany demanded Russia demobilise within 12 hours.[16] When Russia failed to comply, Germany declared war on 1 August in support of Austria-Hungary, with Austria-Hungary following suit on 6th; France ordered full mobilisation in support of Russia on 2 August.[17]

German strategy for a war on two fronts against France and Russia was to rapidly concentrate the bulk of its army in the West to defeat France within four weeks, then shift forces to the East before Russia could fully mobilise; this was later known as the Schlieffen Plan.[18] On 2 August, Germany demanded free passage through Belgium, an essential element in achieving a quick victory over France.[19] When this was refused, German forces invaded Belgium on 3 August and declared war on France the same day; the Belgian government invoked the 1839 Treaty of London and in compliance with its obligations under this, Britain declared war on Germany on 4 August.[20][21] On 12 August, Britain and France also declared war on Austria-Hungary; on the 23rd, Japan sided with the Entente, seizing German possessions in China and the Pacific. In November 1914, the Ottoman Empire entered the war on the side of the Alliance, opening fronts in the Caucasus, Mesopotamia and the Sinai Peninsula. The war was fought in and drew upon each powers' colonial empires as well, spreading the conflict to Africa and across the globe. The Entente and its allies would eventually become known as the Allied Powers, while the grouping of Austria-Hungary, Germany and their allies would become known as the Central Powers.

The German advance into France was halted at the Battle of the Marne and by the end of 1914, the Western Front settled into a battle of attrition, marked by a long series of trench lines that changed little until 1917 (the Eastern Front, by contrast, was marked by much greater exchanges of territory). In 1915, Italy joined the Allied Powers and opened a front in the Alps. The Kingdom of Bulgaria joined the Central Powers in 1915 and the Kingdom of Greece joined the Allies in 1917, expanding the war in the Balkans. The United States initially remained neutral, although by doing nothing to prevent the Allies from procuring American supplies whilst the Allied blockade effectively prevented the Germans from doing the same the U.S. became an important supplier of war material to the Allies. Eventually, after the sinking of American merchant ships by German submarines, and the revelation that the Germans were trying to incite Mexico to make war on the United States, the U.S. declared war on Germany on 6 April 1917. Trained American forces would not begin arriving at the front in large numbers until mid-1918, but ultimately the American Expeditionary Force would reach some two million troops.[22]

Though Serbia was defeated in 1915, and Romania joined the Allied Powers in 1916 only to be defeated in 1917, none of the great powers were knocked out of the war until 1918. The 1917 February Revolution in Russia replaced the Tsarist autocracy with the Provisional Government, but continuing discontent at the cost of the war led to the October Revolution, the creation of the Soviet Socialist Republic, and the signing of the Treaty of Brest-Litovsk by the new government in March 1918, ending Russia's involvement in the war. This allowed the transfer of large numbers of German troops from the East to the Western Front, resulting in the German March 1918 Offensive. This offensive was initially successful, but the Allies rallied and drove the Germans back in their Hundred Days Offensive.[23] Bulgaria was the first Central Power to sign an armistice—the Armistice of Salonica on 29 September 1918. On 30 October, the Ottoman Empire capitulated, signing the Armistice of Mudros.[24] On 4 November, the Austro-Hungarian empire agreed to the Armistice of Villa Giusti. With its allies defeated, revolution at home, and the military no longer willing to fight, Kaiser Wilhelm abdicated on 9 November and Germany signed an armistice on 11 November 1918.

World War I was a significant turning point in the political, cultural, economic, and social climate of the world. The war and its immediate aftermath sparked numerous revolutions and uprisings. The Big Four (Britain, France, the United States, and Italy) imposed their terms on the defeated powers in a series of treaties agreed at the 1919 Paris Peace Conference, the most well known being the German peace treaty—the Treaty of Versailles.[25] Ultimately, as a result of the war the Austro-Hungarian, German, Ottoman, and Russian Empires ceased to exist, with numerous new states created from their remains. However, despite the conclusive Allied victory (and the creation of the League of Nations during the Peace Conference, intended to prevent future wars), a Second World War would follow just over twenty years later.
""")
print(generator.extract_gaps())
