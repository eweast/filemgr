import hashlib
import base64
from db.queries import *
from hash_algos.ed2k import ED2KHash

BUFFER_SIZE = 65536


def check_fs_to_db(appconfig):
    bad_files = []

    db_file_names = get_files_from_db(appconfig)

    for r, d, files in os.walk(os.path.join(appconfig.base_directory, "files")):
        for file in files:
            full_path = os.path.join(r, file)
            db_path = full_path.replace(appconfig.base_directory, "")
            db_path = db_path[1:]

            if not db_path in db_file_names:
                bad_files.append(full_path)
                print("\t{} is in file store but does not exist in database!".format(full_path))

    return bad_files


def get_file_data(file):
    """
    Generates hashes for file and other file info such as size, etc.
    """
    # TODO can i use some kind of magic to determine mime type and forego extension?

    fileinfo = {'inputfile': file, 'filesize': os.path.getsize(file), 'hashes': {}}

    ed2k = ED2KHash()
    sha1 = hashlib.sha1()
    md5 = hashlib.md5()
    md4 = hashlib.new('md4')

    f = open(file, 'rb')
    buf = f.read(BUFFER_SIZE)
    while buf != b'':
        md5.update(buf)
        sha1.update(buf)
        md4.update(buf)
        ed2k.update(buf)
        buf = f.read(BUFFER_SIZE)
    f.close()

    sha1b16 = sha1.hexdigest().upper()
    sha1b32 = base64.b32encode(
        base64.b16decode(sha1b16.upper())).decode().upper()
    edonkey = base64.b16encode(ed2k.digest())
    md4hash = md4.hexdigest().upper()
    md5hash = md5.hexdigest().upper()

    fileinfo['hashes']['md4'] = md4hash

    fileinfo['hashes']['ed2k'] = edonkey.decode('utf-8').upper()
    fileinfo['hashes']['sha1b16'] = sha1b16
    fileinfo['hashes']['sha1b32'] = sha1b32
    fileinfo['hashes']['md5'] = md5hash

    parts = os.path.splitext(file.lower())
    ext = ''

    if len(parts) == 2:
        ext = parts[1]

    fileinfo['extension'] = ext.lower()
    fileinfo['file_store_name'] = sha1b32 + fileinfo['extension']

    return fileinfo