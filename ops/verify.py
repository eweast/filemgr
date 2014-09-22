import os
import sqlite3
import shutil
import settings
from db.queries import delete_files_from_db, file_exists_in_database, delete_file_from_db
from db.queries import get_files_from_db
from fs.get_fileinfo import get_fileinfo
from .import_files import import_files_work


def verify():
    print("*** File manager verification ***\n")

    print("Beginning stage 1 (comparing database against file store)...")
    db_to_fs_bad = check_db_to_fs()

    if len(db_to_fs_bad) == 0:
        print("Stage 1 complete. No inconsistencies detected between database and file system.")

    print("\nBeginning stage 2 (comparing file store against database)...")
    fs_to_db_bad = check_fs_to_db()

    if len(fs_to_db_bad) == 0:
        print("Stage 2 complete. No inconsistencies detected between file system and database.")

    if len(fs_to_db_bad) == 0 and len(db_to_fs_bad) == 0:
        print("\n\nNo inconsistencies detected!")
    else:
        # we have to fix things
        print("\n\nFound {:,d} database and {:,d} file system inconsistencies.".format(len(db_to_fs_bad),
                                                                                       len(fs_to_db_bad)))

        fix_it = input("\nDo you want to fix these issues? [Y|n]: ")

        if not fix_it.lower() == 'n':
            print("\nDeleting bad records from database...", end='')
            delete_files_from_db(db_to_fs_bad)

            print("Deleted {:,d} records from database!".format(len(db_to_fs_bad)))

            # set up a clean staging area for files to be imported from
            verify_directory = os.path.join(settings.base_directory, "verify")

            if os.path.isdir(verify_directory):
                shutil.rmtree(verify_directory)

            os.mkdir(verify_directory)

            print("Adding files to database...")
            for file in fs_to_db_bad:
                fileinfo = get_fileinfo(file)

                if file_exists_in_database(fileinfo):
                    # nuke it to be clean
                    delete_file_from_db(fileinfo)

                # move each file to a staging directory, then call import work on it. done
                head, tail = os.path.split(file)

                to_file = os.path.join(verify_directory, tail)

                unique_prefix = 0

                while os.path.isfile(to_file):
                    # file exists, so get a unique name
                    to_file = os.path.join(verify_directory, str(unique_prefix) + "_" + tail)
                    unique_prefix += 1

                shutil.move(file, to_file)

            (files_added_to_database, total_files, files_deleted, files_copied, files_with_duplicate_hashes,
             files_with_invalid_extensions) = import_files_work(verify_directory)

            shutil.rmtree(verify_directory)

            print("\nAdded {:,d} files to database!".format(files_added_to_database))

            print("\n\n*** Repair complete! ***")


def check_fs_to_db():
    bad_files = []

    db_file_names = get_files_from_db()

    for r, d, files in os.walk(os.path.join(settings.base_directory, "files")):
        for file in files:
            full_path = os.path.join(r, file)
            db_path = full_path.replace(settings.base_directory, "")
            db_path = db_path[1:]

            if not db_path in db_file_names:
                bad_files.append(full_path)
                print("\t{} is in file store but does not exist in database!".format(full_path))

    return bad_files


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