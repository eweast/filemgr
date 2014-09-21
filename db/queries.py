import sqlite3
import os
import datetime
import settings




def get_hash_id_from_hash_name(hash_name):
    conn = sqlite3.connect(settings.database_file)
    c = conn.cursor()
    c.execute(
        "SELECT hashID FROM hashtypes WHERE hashname = ?;", (hash_name,))

    row = c.fetchone()

    conn.close()

    if row is None:
        return -1
    else:
        return int(row[0])


def check_file_exists_in_database(hash_id, hash_value):
    conn = sqlite3.connect(settings.database_file)
    c = conn.cursor()
    c.execute(
        "SELECT files.filepath, files.filesize FROM filehashes INNER JOIN files ON files.fileID = filehashes.fileID "
        "WHERE filehashes.hashID = ? AND filehashes.filehash = ?;",
        (hash_id, hash_value))

    row = c.fetchone()

    conn.close()

    if row is None:
        db_info = ('', 0)
    else:
        db_info = (row[0], row[1])

    return db_info


def get_database_delta(hash_set, hash_id):
    conn = sqlite3.connect(settings.database_file)
    c = conn.cursor()
    sql = "SELECT files.fileID, files.filepath FROM filehashes INNER JOIN files ON files.fileID = filehashes.fileID WHERE filehashes.hashID = ? AND filehashes.filehash NOT in ({0})".format(
        ', '.join('?' for _ in hash_set))
    params = hash_set
    params.insert(0, str(hash_id))

    c.execute(sql, params)

    rows = c.fetchall()

    conn.close()

    return rows


def get_existing_hash_list(hash_id):
    conn = sqlite3.connect(settings.database_file)
    c = conn.cursor()
    c.execute(
        "SELECT fileID, filehash FROM filehashes WHERE filehashes.hashID = ?;", (hash_id, ))

    existing_hashes = {}

  #   row_count = 0

    record = c.fetchone()

    while record:
        # if row_count % 1000000 == 0:
        #     print("{}: Database rows fetched: {:,d}".format(datetime.datetime.now().strftime('%x %X'), row_count))

        existing_hashes[record[1]] = record[0]
        record = c.fetchone()
      #  row_count += 1

    conn.close()

    return existing_hashes


def get_file_from_db(file_id):
    conn = sqlite3.connect(settings.database_file)
    c = conn.cursor()
    c.execute(
        "SELECT filepath FROM files WHERE fileID = ?;", (file_id, ))

    record = c.fetchone()

    conn.close()

    return record[0]


def add_insert_hashtype(hashtype):
    conn = sqlite3.connect(settings.database_file)

    c = conn.cursor()

    c.execute(
        "SELECT hashID FROM hashtypes WHERE hashtypes.hashname = ?;", (hashtype,))

    row = c.fetchone()

    if row is None:
        # insert last_insert_rowid()
        c.execute("INSERT INTO hashtypes (hashname) VALUES (?);", (hashtype,))

        conn.commit()

        rowid = c.lastrowid
    else:
        rowid = row[0]

    conn.close()

    return rowid


def add_file_to_db(fileinfo):
    conn = sqlite3.connect(settings.database_file)

    c = conn.cursor()

    # check if hashtypes has an entry for each hash in hashes
    hashtypes = {}

    for key in fileinfo['hashes'].keys():
        hashtypes[key] = add_insert_hashtype(key)

    filename = fileinfo['inputfile']
    basefilename = os.path.split(filename)[-1]
    basefilenameparts = os.path.splitext(basefilename)
    file_ext = basefilenameparts[1].lower()

    file_directory = os.path.join('files', fileinfo['hashes']['sha1b32'][0:2], fileinfo['hashes']['sha1b32'] + file_ext)

    # add file to files table
    c.execute("INSERT INTO files (importedfilename,filepath,filesize,comment) VALUES (?,?,?,?);",
              (fileinfo['inputfile'], file_directory, fileinfo['filesize'], ''))

    fileid = c.lastrowid

    # add each hash to file hashes
    for hashtype in hashtypes:
        c.execute("INSERT INTO filehashes (hashID,fileID,filehash) VALUES (?,?,?);",
                  (hashtypes[hashtype], fileid, fileinfo['hashes'][hashtype]))

    conn.commit()

    conn.close()


def file_exists_in_database(fileinfo):
    conn = sqlite3.connect(settings.database_file)
    c = conn.cursor()
    c.execute(
        "SELECT filehashID FROM files, filehashes, hashtypes WHERE hashtypes.hashid = filehashes.hashid "
        "AND files.fileID = filehashes.fileID AND hashtypes.hashname = 'sha1b32' AND filehashes.filehash = ?;",
        (fileinfo['hashes']['sha1b32'],))

    row = c.fetchone()

    conn.close()

    if row is None:
        return False
    else:
        return True


def get_sha1b32_from_database():
    # pull them out and cache on startup or when first pulled?

    conn = sqlite3.connect(settings.database_file)
    c = conn.cursor()

    hash_id = get_hash_id_from_hash_name("sha1b32")

    c.execute("SELECT filehash FROM filehashes WHERE hashid = ?;", (hash_id,))

    rows = c.fetchall()

    conn.close()

    hashes = [row[0] for row in rows]

    return set(hashes)


def init_db():
    # create, setup tables
    #one table is hashname
    #another is for files that references hashname pk
    #this allows for easy expanding if hashname is missing without schema changes
    conn = sqlite3.connect(settings.database_file)

    c = conn.cursor()

    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='hashtypes';")

    row = c.fetchone()

    if row is None:
        print("!!!Database is missing. Creating...")
        c.execute('''CREATE TABLE hashtypes
             (hashID INTEGER PRIMARY KEY AUTOINCREMENT, hashname TEXT)''')

        c.execute('''CREATE TABLE files
             (fileID INTEGER PRIMARY KEY AUTOINCREMENT, importedfilename TEXT,
             filepath TEXT, filesize INTEGER, comment TEXT)''')

        c.execute('''CREATE TABLE filehashes
             (filehashID INTEGER PRIMARY KEY AUTOINCREMENT, hashID INTEGER, fileID INTEGER, filehash TEXT)''')

        conn.commit()

    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='importedpaths';")

    row = c.fetchone()

    if row is None:
        print("!!!Table 'importedpaths' is missing!. Creating...")
        c.execute('''CREATE TABLE importedpaths (pathID INTEGER PRIMARY KEY AUTOINCREMENT, importedpath TEXT,
                  imported_date TEXT, files_added_to_database INTEGER, total_files INTEGER, files_deleted INTEGER,
                  files_copied INTEGER, files_with_duplicate_hashes INTEGER, files_with_invalid_extensions INTEGER);''')

        conn.commit()

    #add indexes

    c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type = 'index';")

    row = c.fetchone()

    if row[0] == 0:
        print("!!!Indexes are missing. Creating...")
        c.execute('CREATE INDEX "IX_filehashes" ON "filehashes" ("filehash")')
        print("!File hash index created")
        c.execute('CREATE INDEX "IX_fileID" ON "filehashes" ("fileID")')
        print("!FileID index created")
        c.execute('CREATE UNIQUE INDEX "IU_filepath" ON "files" ("filepath", "filesize")')
        print("!File path/file size index created")
        c.execute('CREATE UNIQUE INDEX "IU_hashID_fileID" ON "filehashes" ("hashID", "filehash")')
        print("!HashID/file hash index created\n")
        c.execute('CREATE INDEX "IX_hashID" ON "filehashes" ("hashID")')
        print("!File hash index created")

        conn.commit()

    conn.close()


def add_import_path_to_db(path_name, files_added_to_database, total_files, files_deleted, files_copied,
                          files_with_duplicate_hashes, files_with_invalid_extensions):
    conn = sqlite3.connect(settings.database_file)

    c = conn.cursor()

    c.execute(
        "INSERT INTO importedpaths (importedpath, imported_date, files_added_to_database, total_files, files_deleted, files_copied, files_with_duplicate_hashes, files_with_invalid_extensions) VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
        (path_name, datetime.datetime.now(), files_added_to_database, total_files, files_deleted, files_copied,
         len(files_with_duplicate_hashes), len(files_with_invalid_extensions)))

    conn.commit()

    conn.close()


def check_import_path_in_db(path_name):
    conn = sqlite3.connect(settings.database_file)

    c = conn.cursor()

    c.execute("SELECT imported_date FROM importedpaths WHERE importedpath = ? ORDER BY imported_date DESC;",
              (path_name,))

    rows = c.fetchall()

    conn.close()
    #2014-02-05 10:22:30.214031
    dates = [datetime.datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S.%f').strftime('%x %X') for row in rows]

    return dates


def generate_hash_list(hash_type, suppress_file_info):
    outfile = os.path.join(settings.base_directory,
                           "Exported hash list_" + datetime.datetime.now().strftime("%H%M%S%f") + '.tsv')

    file_count = 0

    conn = sqlite3.connect(settings.database_file)

    file_cursor = conn.execute("SELECT files.filepath, files.filesize, files.fileID FROM files ORDER BY fileID")

    if hash_type == 'all':
        sql = 'SELECT hashid, hashname FROM hashtypes ORDER BY hashname ASC'
    else:
        sql = 'SELECT hashid, hashname FROM hashtypes WHERE hashname = "{}" ORDER BY hashname ASC'.format(hash_type)

    hash_types_cursor = conn.execute(sql)

    with open(outfile, 'w+', encoding="utf-16") as logfile:
        header = ['relative_path', 'file_size']

        if suppress_file_info:
            header.clear()

        hash_types = {}

        for hash_type_row in hash_types_cursor:
            header.append(hash_type_row[1])
            hash_types[hash_type_row[0]] = hash_type_row[1]

        logfile.write('\t'.join(header) + "\n")

        for file_row in file_cursor:
            file_count += 1
            file_id = file_row[2]

            # hash_types contains the id and hash name for all known hashes. for each of those, get that hash for
            # active file. if not present, tell the user

            row_values = [file_row[0], str(file_row[1])]  # this is what will build out each row

            if suppress_file_info:
                row_values.clear()

            for hash_id in sorted(hash_types,
                                  key=hash_types.get):  # sort it according to the hash names so the order is correct
                hash_cursor = conn.execute(
                    "SELECT filehashes.filehash, hashtypes.hashname FROM hashtypes INNER JOIN filehashes ON "
                    "filehashes.hashID = hashtypes.hashID WHERE filehashes.fileID = ? AND filehashes.hashID = ? "
                    "ORDER BY hashtypes.hashname ASC;",
                    (file_id, hash_id))
                row = hash_cursor.fetchone()
                if not row is None:
                    row_values.append(row[0])
                else:
                    row_values.append("Hash '{}' missing in database!".format(hash_types[hash_id]))
                hash_cursor.close()

            logfile.write('\t'.join(row_values) + "\n")

    conn.close()

    return file_count, outfile


def get_hash_from_hash_id_and_file_id(hash_id, file_id):
    conn = sqlite3.connect(settings.database_file)
    c = conn.cursor()
    c.execute(
        "SELECT filehashes.filehash FROM filehashes WHERE filehashes.hashID = ? AND filehashes.fileID = ?;",
        (hash_id, file_id))

    row = c.fetchone()

    conn.close()

    if row is None:
        return False
    else:
        return row[0]


def get_stats(stats_level):
    # total files
    # total size

    total_store_files = 0
    total_store_size = 0

    conn = sqlite3.connect(settings.database_file)
    c = conn.cursor()
    c.execute("SELECT COUNT(fileID) FROM files")

    row = c.fetchone()

    total_db_files = row[0] or 0

    c.execute("SELECT sum(filesize) FROM files")

    row = c.fetchone()

    total_db_size = row[0] or 0

    conn.close()

    if stats_level == 'full':
        for r, d, files in os.walk(os.path.join(settings.base_directory, "files")):
            total_store_files += len(files)
            for file in files:
                total_store_size += os.path.getsize(os.path.join(r, file))

    return total_db_files, total_db_size, total_store_files, total_store_size


def check_db_to_fs():
    conn = sqlite3.connect(settings.database_file)
    c = conn.cursor()
    c.execute("SELECT fileid, filepath FROM files ORDER BY filepath")

    bad_files = []

    for row in c:
        full_path = os.path.join(settings.base_directory, row[1]).lower()
        if not os.path.isfile(full_path):
            bad_files.append(row[0])
            print("\t{} is in database but does not exist in file store!".format(full_path))

    conn.close()

    return bad_files


def get_files_from_db():
    conn = sqlite3.connect(settings.database_file)
    c = conn.cursor()
    c.execute("SELECT filepath FROM files")

    file_names = []

    for row in c:
        file_names.append(row[0])

    conn.close()

    return file_names


def get_fileid_from_fileinfo(fileinfo):
    conn = sqlite3.connect(settings.database_file)
    c = conn.cursor()

    hashid = get_hash_id_from_hash_name('sha1b32')

    c.execute("SELECT fileid FROM FILEHASHES WHERE hashID = ? AND filehash = ?;",
              (hashid, fileinfo['hashes']['sha1b32']))

    row = c.fetchone()

    conn.close()

    return row[0]


def delete_files_from_db(files):
    conn = sqlite3.connect(settings.database_file)
    c = conn.cursor()

    sql = "DELETE FROM FILEHASHES WHERE fileID in ({})".format(
        ', '.join('?' for _ in list(files)))

    c.execute(sql, files)

    sql = "DELETE FROM files WHERE fileID in ({})".format(
        ', '.join('?' for _ in list(files)))

    c.execute(sql, files)

    conn.commit()

    conn.close()


def delete_file_from_db(fileinfo):
    conn = sqlite3.connect(settings.database_file)
    c = conn.cursor()

    fileid = get_fileid_from_fileinfo(fileinfo)

    c.execute("DELETE FROM filehashes WHERE fileid = ?;", (fileid,))
    conn.commit()

    c.execute("DELETE FROM files WHERE fileid = ?;", (fileid,))
    conn.commit()

    conn.close()
