import unittest
import networkx as nx
import nltk

from project.generator.test_generator import TestGenerator

class TestGeneratorTest(unittest.TestCase):
    def test_is_there_tag_success(self):
        # Arrange
        mock = "noun"

        # Act
        result = TestGenerator.is_there_tag(mock, "NN")

        # Assert
        self.assertEqual(result, True)

    def test_is_there_tag_fail(self):
        # Arrange
        mock = "beautifully"

        # Act
        result = TestGenerator.is_there_tag(mock, "NN")

        # Assert
        self.assertEqual(result, False)

    def test_build_graph(self):
        # Arrange
        mock_first_sentence = "first sentence"
        mock_second_sentence = "second sentence"

        expected = nx.Graph()
        expected.add_nodes_from([mock_first_sentence, mock_second_sentence])
        lev_distance = nltk.edit_distance(mock_first_sentence, mock_second_sentence)
        expected.add_edge(mock_first_sentence, mock_second_sentence, weight=lev_distance)


        # Act
        result = TestGenerator.build_graph([mock_first_sentence, mock_second_sentence])

        # Assert
        self.assertEqual(result.adj == expected.adj and result.nodes == expected.nodes and result.graph == expected.graph, True)

    def test_prepare_test_sentences(self):
        # Arrange
        mock_text = """
        World War II or the Second World War, often abbreviated as WWII or WW2, was a global conflict that lasted from 1939 to 1945. The vast majority of the world's countries, including all of the great powers, fought as part of two opposing military alliances: the Allies (lead by the Soviet Union, United Kingdom, United States and China) and the Axis (lead by Germany, Japan, and Italy). Many participants threw their economic, industrial, and scientific capabilities behind this total war, blurring the distinction between civilian and military resources. Aircraft played a major role, enabling the strategic bombing of population centres and the delivery of the only two nuclear weapons ever used in war.

World War II was by far the deadliest conflict in human history; it resulted in 70 to 85 million fatalities, mostly among civilians. Tens of millions died due to genocides (including the Holocaust), starvation, massacres, and disease. In the wake of the Axis defeat, Germany and Japan were occupied, and war crimes tribunals were conducted against German and Japanese leaders.

The causes of World War II are debated, but contributing factors included the Second Italo-Ethiopian War, Spanish Civil War, Second Sino-Japanese War, Soviet-Japanese border conflicts, rise of fascism in Europe and rising European tensions since World War I. World War II is generally considered to have begun on 1 September 1939, when Nazi Germany, under Adolf Hitler, invaded Poland. The United Kingdom and France subsequently declared war on Germany on 3 September. Under the Molotov-Ribbentrop Pact of August 1939, Germany and the Soviet Union had partitioned Poland and marked out their "spheres of influence" across Finland, Estonia, Latvia, Lithuania and Romania. From late 1939 to early 1941, in a series of campaigns and treaties, Germany conquered or controlled much of continental Europe, and formed the Axis alliance with Italy and Japan (with other countries later). Following the onset of campaigns in North Africa and East Africa, and the fall of France in mid-1940, the war continued primarily between the European Axis powers and the British Empire, with war in the Balkans, the aerial Battle of Britain, the Blitz of the United Kingdom, and the Battle of the Atlantic. On 22 June 1941, Germany led the European Axis powers in an invasion of the Soviet Union, opening the Eastern Front, the largest land theatre of war in history.

        """
        most_important_result = "World War II or the Second World War, often abbreviated as WWII or WW2, was a global conflict that lasted from 1939 to 1945."

        # Act
        result = TestGenerator(mock_text)
        result = result.results[0][0]
        result.replace('\n', '')
        result = result.lstrip()

        # Assert
        self.assertEqual(most_important_result, result)