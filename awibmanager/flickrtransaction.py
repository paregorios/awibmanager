import flickrapi
import json
import sys
from os.path import basename, isfile, splitext

class FlickrTransaction():
	""" Models a transaction with the Flickr API """

	def __init__(self, key=None, secret=None, auth=True):

		self.auth = None
		self.emsg = ''
		self.flickr = None
		self.key = ''
		self.private = ''
		self.uploaded = []

		if key is not None:
			self.key = key
		if secret is not None:
			self.secret = secret
		if auth:
			self.authenticate()
		# note this leaves self.auth == None if auth parameter was False

	def authenticate(self, format='etree'):

		if self.key!='' and self.secret!='':
			try:
				self.flickr = flickrapi.FlickrAPI(self.key, self.secret, format=format)
				(token, frob) = self.flickr.get_token_part_one(perms='delete')
				if not token: raw_input("Press ENTER after you authorized this program to connect to your Flickr account.")
				self.flickr.get_token_part_two((token, frob))
				self.auth = True
			except flickrapi.FlickrError, err:
				self.emsg = err.message
				self.auth = False

			except:
				raise

	def delete(self, photoid):
		self.emsg=''
		funcn = "photos_delete"
		try:
			func = getattr(self.flickr, funcn)
			resp = func(api_key=self.key, photo_id=photoid)
			if resp.attrib['stat']=='ok':
				# remove upload from list
				self.uploaded = [x for x in self.uploaded if x != photoid]
			return resp
		except:
			raise

	def getList(self, listname):

		self.emsg=''
		funcn = "%s_getList" % listname
		try:
			func = getattr(self.flickr, funcn)
			self.rawresp = func(api_key=self.key)
			return self.rawresp

		except AttributeError:
			self.emsg = "FlickrTransaction.getList() could not find a function named %s in the flickrapi package" % funcn
			return None

		except flickrapi.FlickrError, err:
			self.emsg = err.message
			return None


	def upload(self, filepath, title='', description='', tags='', public=0):
		""" upload a file to flickr """

		self.emsg = ''
		if isfile(filepath):
			fn = basename(filepath)
			r, e = splitext(fn)
			if title=='': title=r
			try:
				resp = self.flickr.upload(filename=filepath, title=title, description=description, tags=tags, is_public=public)
				if resp.attrib['stat']=='ok':
					pid = resp.find('.//photoid').text
					self.uploaded.append(pid)
					return pid
				else:
					print "WHAM: %s" % resp.attrib['stat']
					return None
			except flickrapi.FlickrError, err:
				self.emsg = err.message
				print "BAM %s" % self.emsg
				return None
		else:
			print "%s is not a valid file" % filepath






