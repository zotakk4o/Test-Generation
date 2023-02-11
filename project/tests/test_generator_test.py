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