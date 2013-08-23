import flickrapi
import json

class FlickrTransaction():
	""" Models a transaction with the Flickr API """

	def __init__(self, key=None, secret=None, auth=True):

		self.auth = None
		self.emsg = ''
		self.flickr = None
		self.key = ''
		self.private = ''

		if key is not None:
			self.key = key
		if secret is not None:
			self.secret = secret
		if auth:
			self.authenticate()
		# note this leaves self.auth == None if auth parameter was False

	def authenticate(self, format='json'):

		if self.key!='' and self.secret!='':
			try:
				self.flickr = flickrapi.FlickrAPI(self.key, self.secret, format=format)
				(token, frob) = self.flickr.get_token_part_one(perms='write')
				if not token: raw_input("Press ENTER after you authorized this program to connect to your Flickr account.")
				self.flickr.get_token_part_two((token, frob))
				self.auth = True
			except flickrapi.FlickrError, err:
				self.emsg = err.message
				self.auth = False

			except:
				raise

	def getList(self, listname):

		self.emsg=''
		funcn = "%s_getList" % listname
		try:
			func = getattr(self.flickr, funcn)
			self.rawresp = func(api_key=self.key)
			return self.__parseResp__()

		except AttributeError:
			self.emsg = "FlickrTransaction.getList() could not find a function named %s in the flickrapi package" % funcn
			return None

		except flickrapi.FlickrError, err:
			self.emsg = err.message
			return None

	def __parseResp__(self, format='json'):

		self.emsg = ''
		self.resp = None
		result = None
		if format=='json':
			if self.rawresp[:14] == "jsonFlickrApi(":
				jstr = self.rawresp[14:-1]
				self.resp = json.loads(jstr)
				if self.resp['stat'] == 'fail':
					self.emsg = "Flickr API responded with failure message: %s: %s" \
								% (self.resp['code'], self.resp['message'])
				else:
					result = self.resp
		return result



