import re
from . import *
import settings


def import_files(directories):
    """
    Attempts to recursively import files from values in directories and writes log files with actions taken
    @param directories: a list of directories to import from
    """
    print("Importing from '{}'".format(",".join(directories)))
    for directory in directories:
        directory = directory.strip()
        if os.path.isdir(directory):

            import_history = check_import_path_in_db(directory)

            if len(import_history) > 0:
                answer = input(
                    "\n\n**** '{}' has already been imported on:\n\n{}\n\nContinue: [y|N]: ".format(directory,
                                                                                                    '\n'.join(
                                                                                                        import_history)))
                if not answer.lower() == 'y':
                    print("**** Skipping '{}'\n".format(directory))
                    continue

            (files_added_to_database, total_files, files_deleted, files_copied, files_with_duplicate_hashes,
             files_with_invalid_extensions) = import_files_work(directory)

            add_import_path_to_db(directory, files_added_to_database, total_files, files_deleted,
                                  files_copied, files_with_duplicate_hashes, files_with_invalid_extensions)

            print(
                '\n' + '*' * 4 + """ {:,d} total files found. {:,d} copied to file store and {:,d} files were added to the database. {:,d} files had duplicate hashes. {:,d} files had invalid extensions (see log file for details)""".format(
                    total_files, files_copied, files_added_to_database, len(files_with_duplicate_hashes),
                    len(files_with_invalid_extensions)))

            directory_clean = re.sub('[^\w\-_\. ]', '_', directory)

            logfile_name = os.path.join(settings.base_directory,
                                        "Import log for " + directory_clean + " " + datetime.datetime.now().strftime(
                                            "%H%M%S%f") + '.txt')

            with open(logfile_name, 'w+', encoding="utf-16") as logfile:
                logfile.write('Directory processed: {}\n\n'.format(directory))
                logfile.write('Files found: {:,d}\n'.format(total_files))
                logfile.write('Files copied to file store: {:,d}\n'.format(files_copied))
                logfile.write('Files added to database: {:,d}\n'.format(files_added_to_database))

                logfile.write('Files with duplicate hashes: {:,d}\n\n'.format(len(files_with_duplicate_hashes)))

                if files_deleted > 0:
                    logfile.write('Number of deleted files: {:,d}\n\n'.format(files_deleted))

                logfile.write('*' * 78 + '\n\n')

                logfile.write('The following files had duplicate hashes and were not imported:\n\n')
                for item in files_with_duplicate_hashes:
                    logfile.write("{}\n".format(item))

                logfile.write('\n\nThe following files had invalid extensions and were not imported:\n\n')
                for item in files_with_invalid_extensions:
                    logfile.write("{}\n".format(item))

            if settings.delete_existing and files_deleted > 0:
                print(' ' * 5 + '{:,d} files were deleted'.format(files_deleted))
        else:
            print("\t'{}' does not exist!".format(directory))

    # after import, tell the user to see generated logs (one per directory) in the main directory
    # but only if we actually attempted to import something
    if len(directories) > 0 and 'logfile_name' in locals():
        print("\n\nSee log files in {} for details.".format(settings.base_directory))


def import_files_work(dirname):
    files_with_invalid_extensions = []  # list of files we didn't import.

    total_files = 0
    files_added_to_database = 0
    files_deleted = 0
    files_with_duplicate_hashes = []
    files_copied = 0

    # Looking up each hash is sllllllow, so pull em all in as a set and just look there!
    print("Getting existing hashes from database...", end='')
    existing_hashes = get_sha1b32_from_database()

    print("Got {:,d} hashes from database. Looking for files.\n".format(len(existing_hashes)))

    for dirpath, dirnames, files in os.walk(dirname, topdown=False):

        total_files += len(files)

        file_counter = 0

        if len(files) > 0:
            safeprint("\n\tFound {:,d} files in {}. Processing...".format(len(files), dirpath))

            #   logger.info("Found {:,d} files in {}".format(len(files), dirpath))

        for name in files:
            full_path_name = os.path.join(dirpath, name)

            file_counter += 1

            if os.path.isfile(full_path_name):

                if os.path.getsize(full_path_name) == 0:
                    safeprint("\t\tDeleting 0 byte file '{}'.".format(full_path_name))
                    os.remove(full_path_name)
                    continue

                parts = os.path.splitext(name.lower())
                if len(parts) == 2:
                    ext = parts[1]

                    # some files are always bad, so just make em go away.
                    if ext in auto_delete_extensions:
                        safeprint(
                            '\t\t({} [{:,d}/{:,d}]): File {} has an autonuke extension. Deleting...'.format(
                                datetime.datetime.now().strftime('%x %X'),
                                file_counter,
                                len(files), full_path_name))
                        os.remove(full_path_name)
                        continue

                    if ext in extensions:
                        # logger.info(
                        #     "{} before fileinfo = get_file_data(full_path_name)".format(
                        #         datetime.datetime.now().strftime('%x %X')))

                        fileinfo = get_file_data(full_path_name)

                        # logger.info("{} after fileinfo = get_file_data(full_path_name)".format(
                        #     datetime.datetime.now().strftime('%x %X')))

                        if not fileinfo['hashes']['sha1b32'] in existing_hashes:
                            files_added_to_database += 1

                            safeprint("\t\t({} [{:,d}/{:,d}]): '{}' does not exist in database! Adding...".format
                                      (datetime.datetime.now().strftime('%x %X'),
                                       file_counter,
                                       len(files),
                                       full_path_name))

                            # since this is a new file, we add it to our set for future import operations
                            existing_hashes.add(fileinfo['hashes']['sha1b32'])

                            add_file_to_db(fileinfo)
                        else:
                            pass  # do anything else here? should i check if file exists in file system? who cares tho
                            # as this syncs it up maybe here is where you do extra hashing of what is on file
                            #  system to make sure the 2 match, properly named, etc

                        # logger.info("{} before copied = copy_file_to_store(fileinfo)):".format(
                        #     datetime.datetime.now().strftime('%x %X')))

                        copied = copy_file_to_store(fileinfo)

                        if copied:
                            safeprint(
                                '\t\t({} [{:,d}/{:,d}]): File with SHA-1 Base32 hash {} does not exist in file store! Copying {:,d} bytes...'.format(
                                    datetime.datetime.now().strftime('%x %X'),
                                    file_counter,
                                    len(files), fileinfo['hashes']['sha1b32'], fileinfo['filesize']))

                        # logger.info("{} after copied = copy_file_to_store(fileinfo)):".format(
                        #     datetime.datetime.now().strftime('%x %X')))

                        if not copied:
                            files_with_duplicate_hashes.append(full_path_name)
                        else:
                            files_copied += 1

                        if len(settings.copy_new_destination) > 0 and copied:
                            if not os.path.exists(settings.copy_new_destination):
                                os.mkdir(settings.copy_new_destination)

                            # TODO should this create the 2 char structure too? for now, just copy it

                            copy_name = os.path.join(settings.copy_new_destination, name)

                            unique_prefix = 0

                            while os.path.isfile(copy_name):
                                # file exists, so get a unique name
                                copy_name = os.path.join(settings.copy_new_destination,
                                                         str(unique_prefix) + "_" + name)
                                unique_prefix += 1

                            shutil.copyfile(full_path_name, copy_name)

                            outfile = os.path.join(settings.copy_new_destination,
                                                   "!!" + datetime.datetime.now().strftime(
                                                       "%Y-%m-%d") + " File copy log " + '.txt')
                            with open(outfile, 'a', encoding="utf-16") as logfile:
                                logfile.write(
                                    "{}: Copied {} to {}.\n".format(datetime.datetime.now(), full_path_name, copy_name))

                        if settings.delete_existing:
                            safeprint("\t\t({} [{:,d}/{:,d}]): Deleting '{}'...".format(
                                datetime.datetime.now().strftime('%x %X'),
                                file_counter,
                                len(files),
                                full_path_name))

                            if settings.delete_existing == 'yes':
                                os.remove(full_path_name)

                            files_deleted += 1
                    else:
                        files_with_invalid_extensions.append(os.path.join(dirpath, name))

        if settings.delete_empty_directories:
            if not os.listdir(dirpath):
                safeprint("\t\t({} [{:,d}/{:,d}]): Deleting empty directory '{}'...".format(
                    datetime.datetime.now().strftime('%x %X'), file_counter, len(files), dirpath))
                if settings.delete_empty_directories == 'yes':
                    os.rmdir(dirpath)

    return (files_added_to_database, total_files, files_deleted, files_copied, files_with_duplicate_hashes,
            files_with_invalid_extensions)


def copy_file_to_store(fileinfo):
    """Checks datastore for a file with identical sha1b32 hash.
    if one exists, optionally delete the source file
    optionally copy new file to separate directory for sharing purposes
    """

    filename = fileinfo['inputfile']
    base_filename = os.path.split(filename)[-1]
    base_filename_parts = os.path.splitext(base_filename)
    file_ext = base_filename_parts[1].lower()

    files_directory = os.path.join(settings.base_directory, 'files')

    file_directory = os.path.join(files_directory, fileinfo['hashes']['sha1b32'][0:2])

    if not os.path.exists(file_directory):
        os.mkdir(file_directory)

    target_filemask = os.path.join(file_directory, fileinfo['hashes']['sha1b32'] + '*')

    dest_filename = os.path.join(file_directory, fileinfo['hashes']['sha1b32'] + file_ext)

    listing = glob.glob(target_filemask)

    file_copied = False

    if len(listing) == 0:
        shutil.copyfile(filename, dest_filename)
        file_copied = True

    return file_copied