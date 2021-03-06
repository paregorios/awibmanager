import datetime
import errno
from flickrapi import FlickrAPI, FlickrError
from flickrauth import API_KEY, API_SECRET
from lxml import etree
from os import makedirs
from os.path import abspath, exists, isdir, isfile, join, splitext
from PIL import Image, ImageCms
import re
import simplejson as json
import sys
import urllib2

RX_FLICKR_URL = re.compile('^(http:\/\/www\.flickr\.com\/photos\/[^\/]+\/)(\d+)\/?$')
RX_FLICRK_URL_SET = re.compile('^(http:\/\/www\.flickr\.com\/photos\/[^\/]+\/)(\d+)\/in\/set-(\d+)\/?$')
RX_PLEIADES_URL = re.compile('^(http:\/\/pleiades\.stoa\.org\/places\/)(\d+)\/?.*$')

PROFILE_SRGB = 'awibmanager/icc/sRGB_IEC61966-2-1_black_scaled.icc'

fields = {
    'copyright' : 
        ("//info[@type='isaw']/copyright-holder", "copyright", "'%s'"),
    'title' : 
        ("//info[@type='isaw']/title", 'Headline', "'%s'"),
    'keywords' : ("//info[@type='isaw']/typology/keyword", "keywords", "'%s'", ('sequence',)),
    'description' : ("//info[@type='isaw']/description", '', "%s"),
    'date' : 
        ("//info[@type='isaw']/date-photographed | //info[@type='isaw']/date-scanned", "CreateDate", "'%s 00:00:01'", ('replace', '-', ':')),
    'creator' : 
        ("//info[@type='isaw']/photographer", "creator", "'%s'", ('alltext',)),
    'ancient' : ("//info[@type='isaw']/geography/photographed-place/ancient-name", '', "%s"),
    'modern' : ("//info[@type='isaw']/geography/photographed-place/modern-name", '',  "%s"),
    'uri' : ("//info[@type='isaw']/geography/photographed-place/uri", '', "%s"),
    'fda' : ("//info[@type='isaw']/fda-handle", '', "%s"),
    'authority' : ("//info[@type='isaw']/authority", '', "%s") }

SPACEPATTERN = u'\s+'

def normalizetext(source):
    """ Condense arbitrary spans of spaces and newlines in a unicode string down 
    to a single space. Returns a unicode string. """
    #return u' '.join(source.replace(u'\n', u' ').strip().split()).strip()
    rex = re.compile(SPACEPATTERN, re.UNICODE)
    return rex.sub(u' ', source).strip()

def getalltext(elem):
    """Create a document-ordered string from all text nodes in an XML element and its child nodes"""
    text = elem.text or ""
    for e in elem:
        text += getalltext(e)
        if e.tail:
            text += e.tail
    return text


def getval(meta, field):
    """
    get the desired field from the metadata file
    """
    xpath = ''
    try:
        xpath = fields[field][0]
    except:
        print "failed to look up in fields where field = '%s', position 0" % field
        raise
    
    if xpath != '':
        val = meta.xpath(xpath)
        return val


def getMemoryProfile(buffer):
    try:
        return ImageCms.core.profile_fromstring(buffer)
    except (IOError, TypeError, ValueError), v:
        raise PyCMSError(v)

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

    def prep_for_flickr(self):
        """ prepares image for upload to flickr """

        # create a PNG
        im_master = Image.open(self.fn_master)
        try:
            pf = ImageCms.core.profile_fromstring(im_master.info['icc_profile'])
        except AttributeError as e:
            raise type(e), type(e)(e.message + " no icc profile defined on master image '%s'" % self.fn_master), sys.exc_info()[2]
        else:
            im_flickr2 = ImageCms.profileToProfile(im_master, pf, PROFILE_SRGB)
            path = join(self.path, 'flickr2')
            try:
                makedirs(path)
            except OSError as exception:
                if exception.errno != errno.EEXIST:
                    raise            
            fn = join(path, self.id + '.png')
            if exists(fn):
                raise IOError("'file exists :'%s'" % fn)
            else:
                im_flickr2.save(fn, format='PNG')
                self.fn_flickr2 = fn
                # subprocess.call("exiftool -tagsFromFile %s %s" % (self.fn_master, fn))

        # create metadata
        self.make_flickr_caption()


    def send_to_flickr(self):
        if isfile(self.fn_flickr2):
            flickr = getFlickr()
            title = ' '.join((self.title, 'by', self.photographers[0]['name'], 'et al.' if len(self.photographers)>1 else ''))
            resp = flickr.upload(filename=self.fn_flickr2, title=title, description=self.flickr_caption, tags=' '.join(self.keywords), is_public=0)



    def logmod(self, mtype, xpath, seq=0, notes=None):
        self.modified = True
        t = (mtype, xpath, seq, notes)
        self.mods.append(t)

    def make_flickr_caption(self):
        """ prepare an awib-style caption as used on flickr """

        caption = ""
        title = ''
        description = ''
        creator = ''
        year = ''
        copyright = ''
        ancient = ''
        modern = ''
        uri = ''
        fda = ''

        meta = self.meta
        
        v = getval(meta, 'title')
        vt = v[0].text
        if vt is not None:
            title = "%s" % vt
            title = normalizetext(title)
            caption += "AWIB-ISAW: %s" % title
            
        v = getval(meta, 'description')
        vt = v[0].text
        if vt is not None:
            description = "%s" % vt
            description = normalizetext(description)
            caption += "\n%s" % description
            
        v = getval(meta, "creator")
        vt = normalizetext(getalltext(v[0]))
        if vt is not None:    
            creator = "%s" % vt
            creator = normalizetext(creator)
            caption += " by %s" % creator
            
        v = getval(meta, "date")
        try:
            vt = v[0].text
        except IndexError:
            print "index error trying to get date"
            raise
            
        if vt is not None:
            year = vt.split('-')[0]
            caption += " (%s)" % year
            
        v = getval(meta, "copyright")
        vt = v[0].text
        if vt is not None:
            copyright = vt
            copyright = normalizetext(copyright)
            caption += "\ncopyright: "
            if len(year) > 0:
                caption += "%s " % year
            caption += "%s (used with permission)" % copyright
            
        v = getval(meta, 'ancient')
        vt = v[0].text
        if vt is not None:
            ancient = "%s" % vt
            
        v = getval(meta, 'modern')
        vt = v[0].text
        if vt is not None:
            modern = "%s" % vt
            
        v = getval(meta, 'uri')
        vt = v[0].text
        if vt is not None:
            if vt .startswith('http://pleiades.stoa.org'):
                uri = vt
            else:
                uri = "http://atlantides.org/batlas/%s" % vt
            
        if len(ancient) > 0 or len(modern) > 0 or len(uri) > 0:
            caption += "\nphotographed place: "
            if len(ancient) > 0:
                caption += "%s " % ancient
            if len(modern) > 0:
                caption += "(%s) " % modern
            if len(uri) > 0:
                caption += "[%s]" % uri
                
        v = getval(meta, 'fda')
        vt = v[0].text
        if vt is not None :
            fda = vt
            caption += "\narchival copy: %s" % fda
            
        v = getval(meta, 'authority')
        vt = v[0].text
        if vt is not None:
            authority = vt
            authority = normalizetext(authority)
            caption += "\nauthority: %s" % authority
            
        caption += "\n\nPublished by the Institute for the Study of the Ancient World as part of the Ancient World Image Bank (AWIB). Further information: [http://www.nyu.edu/isaw/awib.htm]."
    
        self.flickr_caption = caption
        return caption

    def verify_flickr(self):
        try:
            getattr(self, 'flickr_id')
        except:
            pass
        else:
            flickr = getFlickr()
            r = flickr.photos_getInfo(photo_id=self.flickr_id)
            if r.attrib['stat'] != 'ok':
                self.flickr_verified = 'Flickr API reports photo_id=%s not found' % self.flickr_id
                raise FlickrError(self.flickr_verified)
            else:
                self.flickr_verified = True

    def verify_pleiades(self):
        """ verify Pleiades data associated with this image """
        for g in self.geography:
            if 'uri' in g.keys():
                m = RX_PLEIADES_URL.match(g['uri'])
                if m is not None:
                    try:
                        j = self.get_pleiades_json(g['uri'])
                    except urllib2.HTTPError as e:
                        g['verified'] = e.message
                        raise
                    else:
                        if 'verified' not in g.keys():
                            self.logmod('add', join(self.meta.getpath(self.meta.xpath("//*[starts-with(uri, '%s')]" % g['uri'])[0]), 'verified'), notes='verified Pleiades URI')
                        g['verified'] = True
        self.pleiades_verified = True

    def get_pleiades_json(self, uri):
        """ tries to download json associated with the place uri; does runtime caching of results """
        pid = uri.replace('http://pleiades.stoa.org/places/', '')
        try:
            return self.pleiades_json[pid]
        except KeyError:
            jurl = join(uri, 'json')
            try: 
                results = json.load(urllib2.urlopen(jurl))
            except urllib2.HTTPError as e:
                raise type(e), type(e)(e.message + " while trying to get '%s'" % jurl), sys.exc_info()[2]
            else:
                self.pleiades_json[pid] = results
                return results

    def __str__(self):
        """ output a serialized version of this object and its content """

        d = vars(self)
        for k in sorted(d.iterkeys()):
            print "%s: '%s'" % (k, d[k])

