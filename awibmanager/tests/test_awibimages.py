
import unittest
from awibmanager.awibimages import AI

TESTAWIBID = ''
TESTPATH = 'awibmanager/tests/data/pont-du-gard-france'
BADPATH = './boguspath'

class AIInitCase(unittest.TestCase):

    def test_instantiate(self):
        ai = AI(TESTAWIBID)
        self.assertIsInstance(ai, AI)

    def test_path(self):
        ai = AI(TESTAWIBID, TESTPATH)
        self.assertIsInstance(ai, AI)
        self.assertEqual(ai.path, TESTPATH)

    def test_bad_path(self):
        try:
            ai = AI(TESTAWIBID, BADPATH)
        except IOError as e:
            self.assertEqual(e[0], "'./boguspath' is not a directory")




