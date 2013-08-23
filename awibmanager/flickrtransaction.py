import flickrapi

class FlickrTransaction():
	""" Models a transaction with the Flickr API """

	def __init__(self, key=None, secret=None, auth=True):

		self.auth = None
		self.emsg = ''
		self.key = ''
		self.private = ''

		if key is not None:
			self.key = key
		if secret is not None:
			self.secret = secret
		if auth:
			self.authenticate()
		# note this leaves self.auth == None if auth parameter was False

	def authenticate(self):

		if self.key!='' and self.secret!='':
			try:
				self.flickr = flickrapi.FlickrAPI(self.key, self.secret)
				(token, frob) = self.flickr.get_token_part_one(perms='write')
				if not token: raw_input("Press ENTER after you authorized this program to connect to your Flickr account.")
				self.flickr.get_token_part_two((token, frob))
				self.auth = True
			except flickrapi.FlickrError, err:
				self.emsg = err.message
				self.auth = False

			except:
				raise
