import unittest
from project.generator.utils.clean_utils import CleanUtils
from mocks.clean_utils_mock import CleanUtilsMock

class CleanUtilsTests(unittest.TestCase):
    def test_stemmed_tokenized_sentence(self):
        # Arrange
        mock = CleanUtilsMock("World War II or the Second World War, often abbreviated as WWII or WW2, was a global conflict that lasted from 1939 to 1945. I'll make sure this doesn't get broken.")
        expected = ['world', 'war', 'ii', 'second', 'world', 'war', 'often', 'abbrevi', 'wwii', 'ww2', 'global', 'conflict', 'last', '1939', '1945', 'ill', 'make', 'sure', 'get', 'broken']

        # Act
        result = CleanUtils.clean_text(mock.text, True)

        # Assert
        self.assertEqual(result.sort(), expected.sort())

    def test_stemmed_sentence(self):
        # Arrange
        mock = CleanUtilsMock("World War II or the Second World War, often abbreviated as WWII or WW2, was a global conflict that lasted from 1939 to 1945. I'll make sure this doesn't get broken.")
        expected = ['world war ii second world war often abbrevi wwii ww2 global conflict last 1939 1945 ill make sure get broken']

        # Act
        result = CleanUtils.clean_text(mock.text)

        # Assert
        self.assertEqual(result.sort(), expected.sort())

    def test_only_cleaned_sentence(self):
        # Arrange
        mock = CleanUtilsMock(
            "World War II or the Second World War, often abbreviated as WWII or WW2, was a global conflict that lasted from 1939 to 1945. I'll make sure this doesn't get broken.")
        expected = ['world war ii second world war often abbreviated wwii ww2 global conflict lasted 1939 1945 ill make sure get broken']

        # Act
        result = CleanUtils.clean_text(mock.text, False, False)

        # Assert
        self.assertEqual(result.sort(), expected.sort())