"""
Tests for the NameExtractor class.
"""

import unittest
from name_extractor import NameExtractor

class TestNameExtractor(unittest.TestCase):
    """
    Test suite for the NameExtractor class.
    """

    def test_simple_title(self):
        """
        Tests a simple title with a host and guest.
        """
        title = "The Joe Rogan Experience - #123 - John Doe"
        extractor = NameExtractor(title)
        names = extractor.extract_names()
        self.assertEqual(names["host"], "The Joe Rogan Experience")
        self.assertEqual(names["guest"], "John Doe")

    def test_title_with_keyword(self):
        """
        Tests a title with a 'with' keyword.
        """
        title = "Lex Fridman Podcast with Jane Smith"
        extractor = NameExtractor(title)
        names = extractor.extract_names()
        self.assertEqual(names["host"], "Lex Fridman Podcast")
        self.assertEqual(names["guest"], "Jane Smith")

    def test_title_with_delimiter(self):
        """
        Tests a title with a '|' delimiter.
        """
        title = "The Tim Ferriss Show | The Art of the Interview"
        extractor = NameExtractor(title)
        names = extractor.extract_names()
        self.assertEqual(names["host"], "The Tim Ferriss Show")
        self.assertEqual(names["guest"], "The Art of the Interview")

    def test_title_with_no_guest(self):
        """
        Tests a title with no guest.
        """
        title = "A Solo Episode"
        extractor = NameExtractor(title)
        names = extractor.extract_names()
        self.assertEqual(names["host"], "A Solo Episode")
        self.assertEqual(names["guest"], "No Guest")

if __name__ == "__main__":
    unittest.main()
