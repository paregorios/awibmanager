
import unittest
from awibmanager.awibimages import AI

TESTAWIBID = 'isawi-201102172235161'
TESTPATH = 'awibmanager/tests/data/pont-du-gard-france'
BADPATH = './boguspath'
EMPTYPATH = 'awibmanager/tests/data/empty'
BADID = 'jenny-867-5309'

class AIInitCase(unittest.TestCase):

    def test_path(self):
        ai = AI(TESTAWIBID, TESTPATH)
        self.assertIsInstance(ai, AI)
        self.assertEqual(ai.path, TESTPATH)

    def test_bad_path(self):
        try:
            ai = AI(TESTAWIBID, BADPATH)
        except IOError as e:
            self.assertEqual(e[0], "'./boguspath' is not a directory")

    def test_empty_path(self):
        try:
            ai = AI(TESTAWIBID, EMPTYPATH)
        except IOError as e:
            self.assertEqual(e[0], "'awibmanager/tests/data/empty/meta/isawi-201102172235161-meta.xml' is not a file while trying to set metadata filename")


