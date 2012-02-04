#!/usr/bin/env python
"""
picasa_downloader.py: A little script to download a complete Picasa web album.
"""

__author__ = ['Anoop Jacob Thomas', 'Puneeth Chaganti']
__email__ = 'anoopjt@gmail.com'
__license__ = 'GPL'
__version__ = '0.7'
__status__ = 'Development'


import json
import re
import sys
from argparse import ArgumentParser
from BeautifulSoup import BeautifulSoup
from os import listdir, mkdir
from os.path import basename, exists, join
from urllib2 import urlopen
from zipfile import ZipFile

# Based on http://stackoverflow.com/a/3160819
class ProgressBar(object):
    def __init__(self, items):
        self.display_width = 40
        self.items = items

    def update(self, n):
        complete_frac = (float(n+1)/self.items)
        complete = int(complete_frac * self.display_width)
        remaining = self.display_width-complete
        info = '%4.0f%% Done' %(complete_frac * 100,)
        sys.stdout.write('[%s%s]%s' %('-' * complete, ' ' * remaining, info))
        sys.stdout.flush()
        if complete < self.display_width:
            # add 2 to account for brackets [ ]
            sys.stdout.write('\b' * (self.display_width+len(info)+2))
        else:
            sys.stdout.write('\n')

def get_photo_urls(url):
    """ Get individual photo urls and other info, given url of main page.
    """
    content = urlopen(url).read()
    soup = BeautifulSoup(content)
    for script in soup.findAll('script'):
        if 'albumCoverUrl' in script.text:
            break
    script = ''.join(script.text.splitlines())
    json_like = re.findall('{.*}', script)[0]
    F = '"feed":'
    start, end = json_like.find(F)+len(F), json_like.rfind('}}')
    pics_dict = json.loads(json_like[start:end])
    info = [dict(url=pic['media']['content'][0]['url'],
                    size=pic['size'],
                    height=pic['height'],
                    width=pic['width']) for pic in pics_dict['entry']]
    print 'Found %d pictures' %(len(info),)
    return info

def get_size_dir_url(url, size):
    base, pic = url.rsplit('/', 1)
    return '/'.join([base, 's%s' %(size,), pic])

def download_photos(info, location):
    if not exists(location):
        mkdir(location)
    else:
        print 'Using existing location'
    progress_bar = ProgressBar(len(info))
    for i, pic in enumerate(info):
        url = pic['url']
        height = pic['height']
        width = pic['width']
        size = pic['size']

        # Find the dimension to use for getting largest possible picture.
        image_fp, max_size = None, 0
        for dim in (width, height):
            img_fp = urlopen(get_size_dir_url(url, dim))
            content_length = img_fp.headers.get('content-length')
            if content_length > max_size:
                image_fp = img_fp
                max_size = content_length
            if content_length == size:
                break

        if max_size < size:
            print "Couldn't get original size for %s" %(url,)
        fname = join(location, basename(url))
        output = open(fname,'wb')
        output.write(image_fp.read())
        output.close()
        progress_bar.update(i)

def create_zip_file(directory):
    photos = listdir(directory)
    zip_name = '%s.zip' %(basename(directory),)
    print 'Creating zip %s' %(zip_name,)
    with ZipFile(zip_name, 'w') as photo_zip:
        for photo in photos:
            photo_zip.write(join(directory, photo))

if __name__ == '__main__':
    url = raw_input('Enter the Picasa web album/feed url : ')
    info = get_photo_urls(url)
    name_album = raw_input('Enter a path/directory for the album: ')
    download_photos(info, name_album)
    if '--zip' in sys.argv:
        create_zip_file(name_album)
