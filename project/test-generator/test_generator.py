import nltk
from nltk import tag
from nltk import word_tokenize, sent_tokenize
from utils.clean_utils import CleanUtils
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
        items = tag.pos_tag(word_tokenize(sentence))
        items = [val for key, val in items]
        for item in items:
            if search in item:
                return True
        return False

    @staticmethod
    def build_graph(nodes):
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
        sentence_tokens = CleanUtils.clean_text(text)
        self.sentences = [re.sub("[(\[{][^)}\]]*[)\]}]", "", sent.replace(os.linesep, " ")) for sent in
                          CleanUtils.tokenize_sentences(text)]
        graph = self.build_graph(sentence_tokens)

        calculated_page_rank = nx.pagerank(graph, weight='weight')
        indices = argsort(list(calculated_page_rank.values()))[::-1]

        ranked_sentences = [x for _, x in sorted(zip(indices, self.sentences))]

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
                    chunks_removed = order_gaps(original_sentence, chunks_removed, chunks_removed_delimiter)
                    gaps.append((sentence, chunks_removed))

        return gaps

    def extract_bonuses(self):
        bonuses = []
        for sentence, chunked_sentence in self.results:
            dsc_phrases = self.extract_description_phrases(chunked_sentence)
            if dsc_phrases:
                for object_of_description, phrase in dsc_phrases:
                    if len(phrase.strip().split(" ")) > 2:
                        bonuses.append((object_of_description, phrase))

        return bonuses

    def extract_sentence_completion(self):
        questions = []

        for sentence, chunked_sentence in self.results:
            answers = set()
            candidates_removed = 0

            for chunk_name in ["NB", "NBS"]:  # prioritize List of Names over Names
                if candidates_removed == 0:
                    for chunk, pos_tag in chunked_sentence.items():
                        if pos_tag == chunk_name:
                            chunk = chunk.replace(" ,", ",")
                            answers.add(chunk)
                            gaped_sentence = sentence.replace(chunk, "_" * len(chunk))
                            while len(answers) < 4:
                                candidate = self.replace_numbers(list(answers)[-1])
                                if candidate:
                                    answers.add(candidate)
                                else:
                                    break
                            if len(answers) == 4:
                                questions.append(answers)
                                candidates_removed = 1
                                break

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
            "NBS": "{<IN><CD>}",
            "NM": "{<DT>*<JJ.*>*<NNP.*>+(<IN><DT>*<JJ.*>*<NNP.*>+)*}",
            "NB": "{(<NBS><TO|CC|NM|IN><CD|NM>*)"
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
        objects_of_description = []
        descriptions = []
        sentence = description_chunks[0]
        delimiter = "~$~$~"

        for index in range(1, len(description_chunks)):
            desc = description_chunks[index]
            if re.search("\s(is|are|was|were)", desc):
                sentence = sentence.replace(desc, delimiter)
                objects_of_description.append(desc)

        for description in sentence.split(delimiter)[1:]:
            description = sent_tokenize(description.strip())[0]
            if not self.is_there_tag(description, "PRP"):
                descriptions.append(description)

        return zip(objects_of_description, descriptions)

    @staticmethod
    def replace_numbers(num):
        old_num = num
        months = ['January', 'February', 'March', 'April',
                  'May', 'June', 'July', 'August',
                  'September', 'October', 'November', 'December']
        weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for day in weekdays:
            if day in num:
                weekdays.remove(day)
                num = num.replace(day, choice(weekdays))
        for month in months:
            if month in num:
                months.remove(month)
                num = num.replace(month, choice(months))
        if re.findall(r'(^|\s)([0-9]{1,2})\s', num):
            change = list(range(-5, 5))
            for i, number in enumerate(re.finditer(r'(^|\s)([0-9]{1,2})\s', num)):
                old_n = number.group().strip()
                new_n = int(old_n)
                if new_n <= 31:
                    change = list(range(1, 29))
                    if new_n < 29:
                        change.remove(new_n)
                    new_n = choice(change)
                else:
                    new_n += change
                num = (num[:number.start()] + f" {str(new_n)} " + num[number.end():]).replace(" ,", ",").strip()
        if re.findall(r'(^|\s)(\d{3,})\s*', num):
            change = choice(list(range(-5, 5)))
            for i, number in enumerate(re.finditer(r'(^|\s)(\d{3,})\s*', num)):
                old_n = number.group().strip()
                new_n = int(old_n)
                new_n += change
                num = (num[:number.start()] + f" {str(new_n)} " + num[number.end():]).replace(" ,", ",").strip()

        return num if num != old_num else False


gen = TestGenerator("""
World War II (often abbreviated to WWII or WW2), also known as the Second World War, was a global war that lasted from 1939 to 1945.
The vast majority of the world's countries—including all the great powers—eventually formed two opposing military alliances: the Allies and the Axis.
A state of total war emerged, directly involving more than 100 million people from over 30 countries.
The major participants threw their entire economic, industrial, and scientific capabilities behind the war effort, blurring the distinction between civilian and military resources.
World War II was the deadliest conflict in human history, marked by 50 to 85 million fatalities, most of whom were civilians in the Soviet Union and China.
It included massacres, the genocide of the Holocaust, strategic bombing, premeditated death from starvation and disease, and the only use of nuclear weapons in war.
Japan, which aimed to dominate Asia and the Pacific, was at war with China by 1937, though neither side had declared war on the other.
World War II is generally said to have begun on 1 September 1939, with the invasion of Poland by Germany and subsequent declarations on Germany by France and the United Kingdom.
From late 1939 to early 1941, in a series of campaigns and treaties, Germany conquered or controlled much of continental Europe, and formed the Axis alliance with Italy and Japan.
Under the Molotov–Ribbentrop Pact of August 1939, Germany and the Soviet Union partitioned and annexed territories of their European neighbours, Poland, Finland, Romania and the Baltic states.
Following the onset of campaigns in North Africa and East Africa, and the fall of France in mid 1940, the war continued primarily between the European Axis powers and the British Empire. War in the Balkans, the aerial Battle of Britain, the Blitz, and the long Battle of the Atlantic followed. On 22 June 1941, the European Axis powers launched an invasion of the Soviet Union, opening the largest land theatre of war in history. This Eastern Front trapped the Axis, most crucially the German Wehrmacht, into a war of attrition. In December 1941, Japan launched a surprise attack on the United States and European colonies in the Pacific. Following an immediate U.S. declaration of war against Japan, supported by one from Great Britain, the European Axis powers quickly declared war on the U.S. in solidarity with their Japanese ally. Rapid Japanese conquests over much of the Western Pacific ensued, perceived by many in Asia as liberation from Western dominance and resulting in the support of several armies from defeated territories.
The Axis advance in the Pacific halted in 1942 when Japan lost the critical Battle of Midway; later, Germany and Italy were defeated in North Africa and then, decisively, at Stalingrad in the Soviet Union. Key setbacks in 1943, which included a series of German defeats on the Eastern Front, the Allied invasions of Sicily and Italy, and Allied victories in the Pacific, cost the Axis its initiative and forced it into strategic retreat on all fronts. In 1944, the Western Allies invaded German-occupied France, while the Soviet Union regained its territorial losses and turned toward Germany and its allies. During 1944 and 1945 the Japanese suffered major reverses in mainland Asia in Central China, South China and Burma, while the Allies crippled the Japanese Navy and captured key Western Pacific islands.
The war in Europe concluded with an invasion of Germany by the Western Allies and the Soviet Union, culminating in the capture of Berlin by Soviet troops, the suicide of Adolf Hitler and the German unconditional surrender on 8 May 1945. Following the Potsdam Declaration by the Allies on 26 July 1945 and the refusal of Japan to surrender under its terms, the United States dropped atomic bombs on the Japanese cities of Hiroshima and Nagasaki on 6 and 9 August respectively. With an invasion of the Japanese archipelago imminent, the possibility of additional atomic bombings, the Soviet entry into the war against Japan and its invasion of Manchuria, Japan announced its intention to surrender on 15 August 1945, cementing total victory in Asia for the Allies. Tribunals were set up by fiat by the Allies and war crimes trials were conducted in the wake of the war both against the Germans and the Japanese.
World War II changed the political alignment and social structure of the globe. The United Nations (UN) was established to foster international co-operation and prevent future conflicts; the victorious great powers—China, France, the Soviet Union, the United Kingdom, and the United States—became the permanent members of its Security Council. The Soviet Union and United States emerged as rival superpowers, setting the stage for the nearly half-century long Cold War. In the wake of European devastation, the influence of its great powers waned, triggering the decolonisation of Africa and Asia. Most countries whose industries had been damaged moved towards economic recovery and expansion. Political integration, especially in Europe, emerged as an effort to end pre-war enmities and create a common identity.
""", 50)

print(gen.extract_sentence_completion())