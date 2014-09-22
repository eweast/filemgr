import sqlite3
import settings


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