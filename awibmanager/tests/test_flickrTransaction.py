import unittest
from datetime import datetime
from awibmanager.flickrtransaction import FlickrTransaction
from awibmanager.flickrauth import API_KEY, API_SECRET

# test values for key and secret are random, but correct length 
fakekey = "808d178419ca0530256bad11db83e147" 
fakesecret = "c06e45cb34a8052e"  

class FlickrTransactionInitCase(unittest.TestCase):

	def test_instantiate(self):
		ft = FlickrTransaction()
		self.assertIsInstance(ft, FlickrTransaction)

	def test_key(self):
		ft = FlickrTransaction(key=fakekey, secret=fakesecret, auth=False)
		self.assertEqual(ft.key, fakekey)
		self.assertEqual(ft.secret, fakesecret)
		self.assertEqual(ft.auth, None)

	def test_auth_fail(self):
		ft = FlickrTransaction(key=fakekey, secret=fakesecret)
		self.assertFalse(ft.auth)
		self.assertNotEqual(ft.emsg, '')

	def test_auth_succeed(self):
		ft = FlickrTransaction(key=API_KEY, secret=API_SECRET)
		self.assertTrue(ft.auth)
		self.assertEqual(ft.emsg, '')

class FlickrTransactionParseCase(unittest.TestCase):

	def test_func_not_in_flickrapi(self):
		ft = FlickrTransaction(key=API_KEY, secret=API_SECRET)
		if ft is not None:			
			if ft.auth:
				storks = ft.getList('storks')
				print ft.emsg
				self.assertEqual(storks, None)
				self.assertEqual(ft.emsg, 'Flickr API responded with failure message: 112: Method "flickr.storks.getList" not found')

	def test_func_in_flickrapi(self):
		ft = FlickrTransaction(key=API_KEY, secret=API_SECRET)
		if ft is not None:			
			if ft.auth:
				blogs = ft.getList('blogs')
				print ft.emsg	
				self.assertNotEqual(blogs, None)
				self.assertEqual(ft.emsg, '')

class FlickrUploadCase(unittest.TestCase):

	def test_upload(self):
		t = datetime.now()
		fn = 'foo %s' % t.strftime('%Y-%m-%dT%H:%M:%S')
		title = 'foo photo (%s)' % t.strftime('%Y-%m-%dT%H:%M:%S')
		desc = 'foo bar'
		tags = '''foo "foo bar" bar'''
		public = 0
		ft = FlickrTransaction(key=API_KEY, secret=API_SECRET)
		ft.upload(fn, title, desc, tags, public)
