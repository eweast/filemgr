import zipfile
import os
import settings
import shutil
import datetime
from db.queries import get_hash_id_from_hash_name, check_file_exists_in_database, get_existing_hash_list, \
    get_file_from_db, get_hash_from_hash_id_and_file_id


def export_files(export_existing, file_name):
    """
    Copies files from file store to a directory
    @param export_existing: if true, export files in input file that are also in file store, else, export the opposite
    @param file_name: the file to read hash type and hashes from
    """
    hash_file = open(file_name)
    hash_name = hash_file.readline().strip().lower()
    hash_id = get_hash_id_from_hash_name(hash_name)

    if hash_id == -1:
        print("Unknown hash type: '{}'. Export cancelled!".format(hash_name))
        return

    datetime_string = datetime.datetime.now().strftime("%H%M%S%f")
    export_directory = os.path.join(settings.export_directory,
                                    "Export run " + datetime_string + " for {}".format(hash_name))

    if not os.path.exists(export_directory):
        os.makedirs(export_directory)

    log_name = os.path.join(export_directory,
                            "Export log " + datetime_string + '.txt')

    log_file = open(log_name, 'w', encoding="utf-16")

    log_file.write("Looking for hashes in '{}'\n\n".format(file_name))
    log_file.write("Hash type: {}\n".format(hash_name))
    print("\t\tHash type: {}\n".format(hash_name))
    log_file.write("Zip exported: {}\n".format(settings.zip_exported))
    log_file.write("Rename exported: {}\n\n".format(settings.rename_exported))

    if export_existing:
        export_type = "Existing"
    else:
        export_type = "Delta"

    log_file.write("Export operation: {}\n\n".format(export_type))

    log_file.write("Copy log\n\n")

    found_files = 0
    hash_count = 0

    # TODO collect operations in a single list then iterate/copy after so as to remove duplicate code in loops for each
    if export_existing:
        for line in hash_file:
            line = line.strip()
            hash_count += 1

            (file_path, file_size) = check_file_exists_in_database(hash_id, line)

            # TODO This needs cleaned up in regard to the paths. the database should store things in one format
            # right now its all bunged up

            if file_path:
                print(
                    "\t\t({:,d}) File with hash '{}' found! Copying {:,d} bytes...".format(hash_count, line, file_size))
                found_files += 1
                abs_path = os.path.join(settings.base_directory, file_path)

                if not os.path.isfile(abs_path):
                    front, ext = os.path.splitext(abs_path)

                    abs_path = front + ext.lower()

                abs_path = abs_path.replace("\\", "/")

                if settings.rename_exported and not hash_name == 'sha1b32':  # the default is sha1b32

                    out_path = build_new_out_path(export_directory, line, file_path.replace("\\", "/"))
                else:
                    out_path = os.path.join(export_directory, file_path.replace("\\", "/"))

                print("Copying '{}' to '{}'\n".format(abs_path, out_path))
                copy_file(abs_path, log_file, out_path)  # TODO Error handling here
    else:
        print("Getting hashes from file...")
        hashes = [line.strip() for line in hash_file]

        hash_set = set(hashes)  # get rid of any dupes
        hash_count = len(hash_set)

        file_count = 0

        print("Found {:,d} hashes in file!".format(hash_count))

        # sql wont work
        # export entire DB for hash_id to file containing: file_id and hash for hash_id
        # once done, read that into dictionary with hash: fileid
        # loop thru hash_set and remove similar items from dictionary
        # when done, export files remaining in dictionary

        print("Getting existing hashes from database...")
        existing_hash_list = get_existing_hash_list(hash_id)

        print("Found {:,d} hashes in database!".format(len(existing_hash_list)))

        for hash in hash_set:
            if hash in existing_hash_list:
                del existing_hash_list[hash]

        print("After pruning there are {:,d} hashes to export.".format(len(existing_hash_list)))

        for value in existing_hash_list.values():
            # value is fileID for the file, so now we can get info on the file and export
            db_name = get_file_from_db(value)
            if db_name:
                abs_path = os.path.join(settings.base_directory, db_name)
                if not os.path.isfile(abs_path):
                    front, ext = os.path.splitext(abs_path)
                    abs_path = front + ext.lower()

                abs_path = abs_path.replace("\\", "/")

                if settings.rename_exported and not hash_name == 'sha1b32':  # the default is sha1b32
                    # sigh. we have to now get the appropriate hash value from the database and do trickery based on that
                    # we know the file id, so we can get the hash for the corresponding hash_type from the database
                    # since we also know the hash_id

                    new_hash = get_hash_from_hash_id_and_file_id(hash_id, value)

                    out_path = build_new_out_path(export_directory, new_hash, db_name)
                else:
                    out_path = os.path.join(export_directory, db_name.replace("\\", "/"))

               # print("abs_path is {}".format(abs_path))
              #  print("out_path is {}".format(out_path))

                file_count += 1

                print("[{:,d}/{:,d}] Copying '{}' to '{}'\n".format(file_count,len(existing_hash_list), abs_path, out_path))
                copy_file(abs_path, log_file, out_path)  # TODO Error handling here

    hash_file.close()
    log_file.close()

    if settings.zip_exported:

        zip_name = os.path.join(settings.export_directory,
                                "Exported " + hash_name + " " + datetime_string + ".zip")
        print("\t\tZipping files to '{}'\n".format(zip_name))
        z_file = zipfile.ZipFile(zip_name, "w")

        for dirpath, dirnames, filenames in os.walk(export_directory):
            for filename in filenames:
                full_name = os.path.join(export_directory, dirpath, filename)
                if full_name.endswith("txt"):
                    archive_name = os.path.basename(full_name)
                else:
                    parts = full_name.split("\\")
                    archive_name = "\\".join(str(parts[-3:]))

                z_file.write(full_name, archive_name)
        z_file.close()

        print("\t\tRemoving '{} since export was zipped to {}...'\n".format(export_directory, zip_name))
        shutil.rmtree(export_directory)

    print("\n\t\tSaw {:,d} {} hashes in '{}'. Files found: {:,d}. See '{}' for details.".format(hash_count, hash_name,
                                                                                                file_name, found_files,
                                                                                                log_name))


def copy_file(abs_path, log_file, out_path):
    if not os.path.exists(os.path.dirname(out_path)):
        os.makedirs(os.path.dirname(out_path))
    log_file.write("Copying '{}' to '{}'\n".format(abs_path, out_path))
    shutil.copyfile(abs_path, out_path)


def build_new_out_path(export_directory, new_hash, file_name):
    front = "files\\" + new_hash[0:2]
    mid = new_hash
    ext = os.path.splitext(file_name[1])[-1]
    out_path = os.path.join(export_directory, front, mid + ext.lower())
    return out_path