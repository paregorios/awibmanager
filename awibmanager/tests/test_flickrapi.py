import unittest
from flickrapi import FlickrAPI, FlickrError
from awibmanager.flickrauth import API_KEY, API_SECRET

# test values for key and secret are random, but correct length
FAKEKEY = "808d178419ca0530256bad11db83e147"
FAKESECRET = "c06e45cb34a8052e"

class FlickrInitCase(unittest.TestCase):
    """ verify we can instantiate basic flickr api interactions """

    def test_instantiate(self):
        flickr = FlickrAPI(API_KEY, API_SECRET)
        self.assertIsInstance(flickr, FlickrAPI)

    def test_authenticate(self):
        flickr = FlickrAPI(API_KEY, API_SECRET)
        (token, frob) = flickr.get_token_part_one(perms='write')
        if not token: raw_input("Press ENTER after you authorized this program")
        flickr.get_token_part_two((token, frob))

    def test_authenticate_fail(self):
        flickr = FlickrAPI(FAKEKEY, FAKESECRET)
        try:
            (token, frob) = flickr.get_token_part_one(perms='write')
            if not token: raw_input("Press ENTER after you authorized this program")
            flickr.get_token_part_two((token, frob))
        except FlickrError as e:
            self.assertEqual(e[0], u'Error: 100: Invalid API Key (Key not found)')
