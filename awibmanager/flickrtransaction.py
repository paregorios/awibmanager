import flickrapi
import json
import sys
from os.path import basename, isfile, splitext

class FlickrTransactor():
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
		""" walk through the flickr authentication process """
		self.auth = False	
		if self.key!='' and self.secret!='':
			self.flickr = flickrapi.FlickrAPI(self.key, self.secret, format=format)
			(token, frob) = self.flickr.get_token_part_one(perms='delete')
			if not token: raw_input("Press ENTER after you authorized this program to connect to your Flickr account.")
			self.flickr.get_token_part_two((token, frob))
			self.auth = True





