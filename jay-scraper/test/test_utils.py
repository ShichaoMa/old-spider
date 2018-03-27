import unittest
import re
from toolkit import re_search


def format_price(price, regex=re.compile(r"([\d\.]+)")):
    return float(re_search(regex, price, default=0))


class UtilsTest(unittest.TestCase):

    def test_format_price(self):
        self.assertEqual(format_price("$3.12"), 3.12)