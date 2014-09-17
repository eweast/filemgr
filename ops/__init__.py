import shutil
import glob
from fs.queries import *

extensions = {'.jpg', '.avi', '.ram', '.rm', '.wmv', '.pdf', '.mov', '.mp4', '.flv', '.jpe', '.jpeg', '.mpg', '.mpe',
              '.mpeg', '.png', '.3g2', '.3gp', '.asf', '.bmp', '.divx', '.gif', '.jpg', '.m1v', '.vob', '.mod', '.tif',
              '.mkv', '.jp2', '.psd', '.m4v', '.pcx'}

auto_delete_extensions = {'.db', '.com', '.scr', '.htm', '.html', '.url', '.thm', '.tmp', '.ds_store', '.ico', '.rtf',
                          '.doc', '.ini', '.ascii', '.dat', '.svg'}

import sys
def safeprint(s):
    try:
        print(s)
    except UnicodeEncodeError:
        print(s.encode('utf8').decode(sys.stdout.encoding))

    def digest(self):
        if len(self.hashes) == 0:
            return self.md4.digest()
        else:
            m = hashlib.new('md4')
            newhashes = self.hashes + [self.md4.digest()]
            m.update(b''.join(newhashes))
            return m.digest()