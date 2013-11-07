import datetime
from flickrapi import FlickrAPI, FlickrError
from flickrauth import API_KEY, API_SECRET
from lxml import etree
from os.path import isdir, isfile, join
import re
import simplejson as json
import sys
import urllib2

RX_FLICKR_URL = re.compile('^(http:\/\/www\.flickr\.com\/photos\/[^\/]+\/)(\d+)\/?$')
RX_FLICRK_URL_SET = re.compile('^(http:\/\/www\.flickr\.com\/photos\/[^\/]+\/)(\d+)\/in\/set-(\d+)\/?$')
RX_PLEIADES_URL = re.compile('^(http:\/\/pleiades\.stoa\.org\/places\/)(\d+)\/?.*$')


def fileval(root, interstitial, id, tail):
    fn = join(root, interstitial, '-'.join((id, tail)))
    if isfile(fn):
        return fn
    else:
        raise IOError, "'%s' is not a file" % fn

def getFlickr(key=API_KEY, secret=API_SECRET):
    flickr = FlickrAPI(key, secret)
    (token, frob) = flickr.get_token_part_one(perms='write')
    if not token: raw_input("Press ENTER after you authorized this program")
    flickr.get_token_part_two((token, frob))
    return flickr

class AI():
    """ handle all information, behaviors, and avatars of an AWIB image """

    def __init__(self, id, path='.', verify=['pleiades',]):
        """ initialize an AWIB image object by reading data from disk and verifying online sources as necessary """

        self.modified = False
        self.mods = []
        self.flickr_verified = False
        self.pleiades_verified = False
        self.pleiades_json = {}

        # the awib ID is the one ring to rule all these images
        self.id = id

        # determine and verify paths to the files on disk that correspond to this image
        if path is not None:
            if isdir(path):
                self.path = path
                try:
                    self.fn_meta = fileval(path, 'meta', id, 'meta.xml')
                except IOError as e:
                    raise type(e), type(e)(e.message + " while trying to set metadata filename"), sys.exc_info()[2]
                try:
                    self.fn_master = fileval(path, 'masters', id, 'master.tif')
                except IOError as e:
                    raise type(e), type(e)(e.message + " while trying to set master filename"), sys.exc_info()[2]
                try:
                    self.fn_review = fileval(path, 'review-images', id, 'review.jpg')
                except IOError:
                    self.fn_review = None
                try:
                    self.fn_thumb = fileval(path, 'thumbnails', id, 'thumb.jpg')
                except IOError:
                    self.fn_thumb = None
            else:
                raise IOError, "'%s' is not a directory" % path

            # read and parse filesystem metadata
            self.loadxml()

        # determine and validate information about this image in flickr
        if 'flickr' in verify:
            self.verify_flickr()

        # determine and validate information about this image in the FDA

        # determine and validate information about this image in Pleiades
        if 'pleiades' in verify:
            self.verify_pleiades()


        # TBD
        self.__str__()


    def loadxml(self):
        """ load AWIB image data from standard metadata XML file """

        self.photographers = []
        self.keywords = []
        self.geography = []
        full = ''
        family = ''
        given = ''
        f = open(self.fn_meta)
        meta = etree.parse(f)
        self.meta = meta
        f.close()
        w = "//info[@type='isaw']"
        for ele in meta.xpath(join(w, "*")):

            if ele.tag == 'photographer':
                d = {}
                if len(ele) != 0:
                    for sub in ele:
                        d[sub.tag.replace('-', '_')] = sub.text
                elif ele.text is not None:
                    d['name'] = ele.text
                if 'name' not in d.keys() and 'family_name' in d.keys() and 'given_name' in d.keys():
                    d['name'] = ' '.join((d['given_name'], d['family_name']))
                    self.logmod('add', join(meta.getpath(ele), 'name'), len(self.photographers), 'generated full name for photographer from given and family names already in the metadata file')
                if len(d) > 0:
                    self.photographers.append(d)

            elif ele.tag == 'typology':
                if len(ele) != 0:
                    for sub in ele:
                        self.keywords.append(sub.text)

            elif ele.tag == 'geography':
                if len(ele) != 0:
                    for sub in ele:
                        d = {}
                        if len(sub) != 0:
                            d['type'] = sub.tag
                            for subsub in sub:
                                if subsub.tag == 'uri':
                                    m = RX_PLEIADES_URL.match(subsub.text)
                                    if m is not None:
                                        g = m.groups()
                                        uri = join(g[0], g[1])
                                        if subsub.text != uri:
                                            self.logmod('change', meta.getpath(subsub), notes='removed extraneous elements from the Pleiades URI')
                                        d['uri'] = uri
                                elif subsub.text is not None:
                                    d[subsub.tag.replace('-', '_')] = subsub.text
                        if len(d) > 0:
                            self.geography.append(d)

            elif ele.tag == 'flickr-url':
                flickr_url = None
                flickr_id = None
                flickr_set = None
                m = RX_FLICKR_URL.match(ele.text)
                if m is None:
                    m = RX_FLICRK_URL_SET.match(ele.text)
                if m is not None:
                    g = m.groups()
                    flickr_url = join(g[0], g[1])
                    if ele.text != flickr_url:
                        self.logmod('change', meta.getpath(ele), notes='removed extraneous elements from the flickr URL')
                    self.flickr_url = flickr_url                    
                    flickr_id = g[1]
                    if len(g) > 2:
                        flickr_set = g[2]




            elif ele.tag in ['prosopography', 'notes', 'chronology']:
                # suppress these for now
                pass

            else:
                setattr(self, ele.tag.replace('-', '_'), ele.text)

        try:
            getattr(self, 'flickr_url')
            try:
                getattr(self, 'flickr_id')
            except AttributeError:
                if flickr_id is not None:
                    setattr(self, 'flickr_id', flickr_id)
                    self.logmod('add', join(w, 'flickr-id'), notes='created flickr ID as extracted from flickr URL')
            try:
                getattr(self, 'flickr_set')
            except AttributeError:
                if flickr_set is not None:
                    setattr(self, 'flickr_set', flickr_set)
                    self.logmod('add', join(w, 'flickr-set'), notes='created flickr set id as extracted from flickr URL')
        except AttributeError:
            pass


    def logmod(self, mtype, xpath, seq=0, notes=None):
        self.modified = True
        t = (mtype, xpath, seq, notes)
        self.mods.append(t)

    def verify_flickr(self):
        try:
            getattr(self, 'flickr_id')
        except:
            pass
        else:
            flickr = getFlickr()
            r = flickr.photos_getInfo(photo_id=self.flickr_id)
            if r.attrib['stat'] != 'ok':
                raise FlickrError('Flickr API reports photo_id=%s not found' % self.flickr_id)
            else:
                self.flickr_verified = True

    def verify_pleiades(self):
        """ verify Pleiades data associated with this image """
        for g in self.geography:
            print g
            if 'uri' in g.keys():
                print "in"
                m = RX_PLEIADES_URL.match(g['uri'])
                if m is not None:
                    print "match"
                    jurl = join(g['uri'], 'json')
                    try:
                        results = json.load(urllib2.urlopen(jurl))
                    except urllib2.HTTPError as e:
                        g['verified'] = e.message
                    else:
                        if 'verified' not in g.keys():
                            self.logmod('add', join(self.meta.getpath(self.meta.xpath("//*[starts-with(uri, '%s')]" % g['uri'])[0]), 'verified'), notes='verified Pleiades URI')
                        g['verified'] = True
                        s = json.dumps(results, sort_keys=True, indent=4)
                        print '\n'.join([l.rstrip() for l in  s.splitlines()])
        self.pleiades_verified = True

    def get_pleiades_json(self, uri):
        pid = uri.replace('http://pleiades.stoa.org/places/', '')
        try:
            return self.pleiades_json[pid]
        except KeyError:
            jurl = join(g['uri'], 'json')
            

    def __str__(self):
        """ output a serialized version of this object and its content """

        d = vars(self)
        for k in sorted(d.iterkeys()):
            print "%s: '%s'" % (k, d[k])

