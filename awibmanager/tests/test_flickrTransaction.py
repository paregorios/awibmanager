
import os
import unittest
from datetime import datetime
from flickrapi import FlickrError
from lxml import etree
from os import listdir
from os.path import isfile, join
from awibmanager.flickrtransaction import FlickrTransactor
from awibmanager.flickrauth import API_KEY, API_SECRET

# test values for key and secret are random, but correct length 
fakekey = "808d178419ca0530256bad11db83e147" 
fakesecret = "c06e45cb34a8052e"  
DATADIR = 'awibmanager/tests/data'

class FlickrTransactorInitCase(unittest.TestCase):

	def test_instantiate(self):
		ft = FlickrTransactor()
		self.assertIsInstance(ft, FlickrTransactor)

	def test_key(self):
		ft = FlickrTransactor(key=fakekey, secret=fakesecret, auth=False)
		self.assertEqual(ft.key, fakekey)
		self.assertEqual(ft.secret, fakesecret)
		self.assertEqual(ft.auth, None)

	def test_auth_fail(self):
		try:
			ft = FlickrTransactor(key=fakekey, secret=fakesecret)
		except FlickrError, err:
			self.assertEqual(err[0], '100')
			self.assertEqual(err[1], 'Invalid API Key (Key not found)')

	def test_auth_succeed(self):
		ft = FlickrTransactor(key=API_KEY, secret=API_SECRET)
		self.assertTrue(ft.auth)
		self.assertEqual(ft.emsg, '')

class FlickrTransactorParseCase(unittest.TestCase):

	def test_func_not_in_flickrapi(self):
		ft = FlickrTransactor(key=API_KEY, secret=API_SECRET)
		storks = ft.stork_getList()
		self.assertEqual(storks, None)
		self.assertEqual(ft.emsg, 'Error: 112: Method "flickr.storks.getList" not found')

	def test_func_in_flickrapi(self):
		ft = FlickrTransactor(key=API_KEY, secret=API_SECRET)
		panda = ft.panda_getList()
		self.assertEqual(panda.attrib['stat'], 'ok')
		self.assertEqual(ft.emsg, '')

