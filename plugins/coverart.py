""" 
A small plugin to download cover art for any releseas that have a
CoverArtLink relation.


Changelog:

    [2007-04-24] Moved parsing code into here
                 Swapped to QUrl
                 Moved to a list of urls

    [2007-04-23] Moved it to use the bzr picard
                 Took the hack out
                 Added Amazon ASIN support
                 
    [2007-04-23] Initial plugin, uses a hack that relies on Python being
                 installed and musicbrainz2 for the query.

"""

PLUGIN_NAME = 'Cover Art Downloader'
PLUGIN_AUTHOR = 'Oliver Charles'
PLUGIN_DESCRIPTION = '''Downloads cover artwork for releases that have a
CoverArtLink.'''

from picard.metadata import register_album_metadata_processor
from picard.util import partial
from PyQt4.QtCore import QUrl


_AMAZON_IMAGE_HOST = 'images.amazon.com'
_AMAZON_IMAGE_PATH = '/images/P/%s.01.LZZZZZZZ.jpg'
_AMAZON_IMAGE_PATH_SMALL = '/images/P/%s.01.MZZZZZZZ.jpg'


def _coverart_downloaded(album, metadata, release, try_list, data, http, error):
    try:
        if error or len(data) < 1000:
            if error:
                album.log.error(str(http.errorString()))
            coverart(album, metadata, release, try_list)
        else:
            image = ("image/jpeg", data)
            metadata.add("~artwork", image)
            for track in album._new_tracks:
                track.metadata.add("~artwork", image)
    finally:
        album._requests -= 1
        album._finalize_loading(None)


def coverart(album, metadata, release, try_list=None):
    """ Gets the CDBaby URL from the metadata, and the attempts to
    download the album art. """

    # try_list will be None for the first call
    if try_list is None:
        try_list = []

        try:
            for relation_list in release.relation_list:
                if relation_list.target_type == 'Url':
                    for relation in relation_list.relation:
                        if relation.type == 'CoverArtLink':
                            parsedUrl = QUrl(relation.target)
                            try_list.append({
                                'host': str(parsedUrl.host()),
                                'port': parsedUrl.port(80),
                                'path': str(parsedUrl.path())
                            })
        except AttributeError:
            pass

        if metadata['asin']:
            try_list.append({'host': _AMAZON_IMAGE_HOST, 'port': 80,
                'path': _AMAZON_IMAGE_PATH % metadata['asin']
            })
            try_list.append({'host': _AMAZON_IMAGE_HOST, 'port': 80,
                'path': _AMAZON_IMAGE_PATH_SMALL % metadata['asin']
            })

    if len(try_list) > 0:
        # We still have some items to try!
        album._requests += 1
        album.tagger.xmlws.download(
                try_list[0]['host'], try_list[0]['port'], try_list[0]['path'],
                partial(_coverart_downloaded, album, metadata, release, try_list[1:]),
                position=1)


register_album_metadata_processor(coverart)
