
import os
import unittest
from datetime import datetime
from lxml import etree
from os import listdir
from os.path import isfile, join
from awibmanager.flickrtransaction import FlickrTransaction
from awibmanager.flickrauth import API_KEY, API_SECRET

# test values for key and secret are random, but correct length 
fakekey = "808d178419ca0530256bad11db83e147" 
fakesecret = "c06e45cb34a8052e"  
DATADIR = 'awibmanager/tests/data'

def z(progress, done):
    if done:
        print "Done uploading"
    else:
        print "At %s%%" % progress

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
				self.assertEqual(storks, None)
				self.assertEqual(ft.emsg, 'Error: 112: Method "flickr.storks.getList" not found')

	def test_func_in_flickrapi(self):
		ft = FlickrTransaction(key=API_KEY, secret=API_SECRET)
		if ft is not None:			
			if ft.auth:
				panda = ft.getList('panda')
				self.assertEqual(panda.attrib['stat'], 'ok')
				self.assertEqual(ft.emsg, '')

class FlickrUploadCase(unittest.TestCase):
	
	def test_upload(self):
		""" test uploading and deletion of a single photo with bogus metadata """
		t = datetime.now()
		fn = join(DATADIR, 'beneventum/thumbnails/isawi-200906041524591-thumb.jpg')
		title = 'foo photo (%s)' % t.strftime('%Y-%m-%dT%H:%M:%S')
		desc = 'foo bar'
		tags = '''foo "foo bar" bar'''
		public = 0
		ft = FlickrTransaction(key=API_KEY, secret=API_SECRET)
		if ft is not None:
			if ft.auth:
				pid = ft.upload(fn, title, desc, tags, public)
				self.assertNotEqual(pid, None)
				self.assertEqual(ft.emsg, '')
				self.assertEqual(pid, ft.uploaded[-1])
				if pid is not None:
					resp = ft.delete(pid)
					self.assertEqual(resp.attrib['stat'], 'ok')
					self.assertEqual(len(ft.uploaded), 0)

	def test_uploadAWIB(self):
		""" test uploading and deletion of an entire set of AWIB data, including XML metadata """
		imagedir = join(DATADIR, 'pont-du-gard-france')
		where = join(imagedir, 'meta')
		fns = [ join(where,f) for f in listdir(where) if isfile(join(where,f)) ]
		for fn in fns:
			f = open(fn, 'r')
			meta = etree.parse(f)
			f.close()
			if meta.find('.//isaw-publish-cleared').text=='yes':
				w = "//info[@type='isaw'][1]"
				title = meta.xpath(join(w, 'title'))[0].text
				desc = meta.xpath(join(w, 'description'))[0].text
				tags = meta.xpath(join(w, 'typology', 'keyword'))
				tags = ' '.join([e.text for e in tags])
				print tags
				public = 0
				masterfile = join(where, meta.xpath("//image-files[1]/image[@type='master'][1]")[0].attrib['href'])
				ft = FlickrTransaction(key=API_KEY, secret=API_SECRET)
				if ft is not None:
					if ft.auth:
						print "uploading file %s to Flickr" % masterfile
						pid = ft.upload(masterfile, title, desc, tags, public)
						self.assertNotEqual(pid, None)
						self.assertEqual(ft.emsg, '')
						self.assertEqual(pid, ft.uploaded[-1])

			else:
				print "skipping file %s because not marked clear to publish" % fn
