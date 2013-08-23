import unittest
from awibmanager.flickrtransaction import FlickrTransaction
from awibmanager.flickrauth import API_KEY, API_SECRET

# test values for key and secret are random, but correct length 
fakekey = "808d178419ca0530256bad11db83e147" 
fakesecret = "c06e45cb34a8052e"  

class FlickrTransationCase(unittest.TestCase):

	def test_instantiate(self):
		ft = FlickrTransaction()
		self.assertIsInstance(ft, FlickrTransaction)

	def test_key(self):
		ft = FlickrTransaction(key=fakekey, secret=fakesecret, auth=False)
		self.assertEqual(ft.key, fakekey)
		self.assertEqual(ft.secret, fakesecret)

	def test_auth_fail(self):
		ft = FlickrTransaction(key=fakekey, secret=fakesecret)
		self.assertFalse(ft.auth)
		self.assertNotEqual(ft.emsg, '')

	def test_auth_succeed(self):
		ft = FlickrTransaction(key=API_KEY, secret=API_SECRET)
		self.assertTrue(ft.auth)
		self.assertEqual(ft.emsg, '')

