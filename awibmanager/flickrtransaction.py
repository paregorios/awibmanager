from flickrapi import FlickrAPI
import json
import sys
from os.path import basename, isfile, splitext

class FlickrTransactor(FlickrAPI):
	""" Models a transaction with the Flickr API """

	def __init__(self, key=None, secret=None, auth=True, format='etree'):

		self.auth = None

		if key is not None:
			self.origkey = key
		if secret is not None:
			self.origsecret = secret

		if key is not None and secret is not None:
			FlickrAPI.__init__(self, key, secret, format)
			(token, frob) = self.get_token_part_one(perms='delete')
			if not token: raw_input("Press ENTER after you authorized this program to connect to your Flickr account.")
			self.get_token_part_two((token, frob))
			self.auth = True



