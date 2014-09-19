import argparse
import configparser
from sys import exit

from fs.queries import *
from ops.import_files import import_files
from ops.export_files import export_files
from ops.verify import verify

# TODO use pathlib vs os.path calls? this is 3.4 only
# http://docs.sqlalchemy.org/en/rel_0_9/orm/tutorial.html ??
# http://docs.python.org/3.4/howto/logging-cookbook.html

# a list of valid file extensions to import. anything else will be skipped. make it a set in case people add dupes
extensions = {'.jpg', '.avi', '.ram', '.rm', '.wmv', '.pdf', '.mov', '.mp4', '.flv', '.jpe', '.jpeg', '.mpg', '.mpe',
              '.mpeg', '.png', '.3g2', '.3gp', '.asf', '.bmp', '.divx', '.gif', '.jpg', '.m1v', '.vob', '.mod', '.tif',
              '.mkv', '.jp2', '.psd', '.m4v', '.pcx'}

# a list of extensions to delete. If any of these extensions are found in 'extensions' the import will be cancelled
auto_delete_extensions = {'.db', '.com', '.scr', '.htm', '.html', '.url', '.thm', '.tmp', '.ds_store', '.ico', '.rtf',
                          '.doc', '.ini', '.ascii', '.dat', '.svg'}

BUFFER_SIZE = 65536  # 8192 # file reading buffer size 8192 * 64?

# logger = logging.getLogger('filemgr')
# logger.setLevel(logging.CRITICAL)
# fh = logging.FileHandler('filemgr_debug.log')
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# fh.setFormatter(formatter)
# logger.addHandler(fh)


class ApplicationConfiguration():
    """
    Holds configuration values used in various places
    """

    def __init__(self, config, args):
        self.__database_name = config['General']['database_name']
        self.__base_directory = os.path.abspath(args.base_directory) or os.path.abspath(
            config['General']['base_directory']) or os.path.abspath('')
        self.__database_file = os.path.join(self.base_directory, self.database_name)
        self.__delete_existing = args.delete_existing if args.delete_existing is None else False
        self.__copy_new_destination = ''
        self.__export_directory = ''
        self.__rename_exported = False
        self.__zip_exported = False
        self.__delete_empty_directories = ''

    def get_database_name(self):
        return self.__database_name

    def set_database_name(self, database_name):
        self.__database_name = database_name

    database_name = property(get_database_name, set_database_name)

    def get_base_directory(self):
        return self.__base_directory

    def set_base_directory(self, base_directory):
        self.__base_directory = base_directory

    base_directory = property(get_base_directory, set_base_directory)

    def get_database_file(self):
        return self.__database_file

    def set_database_file(self, database_file):
        pass  # todo remove

    database_file = property(get_database_file, set_database_file)

    def get_delete_existing(self):
        return self.__delete_existing

    def set_delete_existing(self, delete_existing):
        self.__delete_existing = delete_existing

    delete_existing = property(get_delete_existing, set_delete_existing)

    def get_delete_empty_directories(self):
        return self.__delete_empty_directories

    def set_delete_empty_directories(self, delete_empty_directories):
        self.__delete_empty_directories = delete_empty_directories

    delete_empty_directories = property(get_delete_empty_directories, set_delete_empty_directories)

    def get_export_directory(self):
        return self.__export_directory

    def set_export_directory(self, export_directory):
        self.__export_directory = export_directory

    export_directory = property(get_export_directory, set_export_directory)

    def get_rename_exported(self):
        return self.__rename_exported

    def set_rename_exported(self, rename_exported):
        self.__rename_exported = rename_exported

    rename_exported = property(get_rename_exported, set_rename_exported)

    def get_zip_exported(self):
        return self.__zip_exported

    def set_zip_exported(self, zip_exported):
        self.__zip_exported = zip_exported

    zip_exported = property(get_zip_exported, set_zip_exported)

    def get_copy_new_destination(self):
        return self.__copy_new_destination

    def set_copy_new_destination(self, copy_new_destination):
        self.__copy_new_destination = copy_new_destination

    copy_new_destination = property(get_copy_new_destination, set_copy_new_destination)


# def generate_missing_hashes(appconfig, file):
# """ Given file, look for missing hashes, generate them, and update the
#     database """
#
#     return "not done yet"


def setup_base_directory(directory):
    try:
        if not os.path.exists(directory):
            print('{} does not exist! Creating...'.format(directory))
            os.mkdir(directory)

        subdir = os.path.join(directory, 'files')

        if not os.path.exists(subdir):
            os.mkdir(subdir)
    except:
        raise


def bytes_to_human(byte_value, to, bsize=1024):
    """convert byte_value to megabytes, etc.
       sample code:
           print('mb= ' + str(bytesto(314575262000000, 'm')))

       sample output:
           mb= 300002347.946
    """

    if byte_value is None:
        return float(0)

    a = {'k': 1, 'm': 2, 'g': 3, 't': 4, 'p': 5, 'e': 6}
    r = float(byte_value)
    for i in range(a[to]):
        r /= bsize

    return r


def dump_stats(appconfig, print_stats):
    print("\n*** Database statistics ***\n")

    if print_stats == 'full':
        print("\t *** Please be patient while file store statistics are calculated. This may take a while! ***\n")

    (total_db_files, total_db_size, total_store_files, total_store_size) = get_stats(appconfig, print_stats)

    print("Total files in database: {:,d}".format(total_db_files))
    print("Total size of files in database: {:,d} bytes ({:,f} MB, {:,f} GB, {:,f} TB)\n".format(total_db_size,
                                                                                                 bytes_to_human(
                                                                                                     total_db_size,
                                                                                                     'm'),
                                                                                                 bytes_to_human(
                                                                                                     total_db_size,
                                                                                                     'g'),
                                                                                                 bytes_to_human(
                                                                                                     total_db_size,
                                                                                                     't')))

    if print_stats == 'full':
        print("Total files in file store: {:,d}".format(total_store_files))
        print("Total size of files in file store: {:,d} bytes ({:,f} MB, {:,f} GB, {:,f} TB)\n".format(total_store_size,
                                                                                                       bytes_to_human(
                                                                                                           total_store_size,
                                                                                                           'm'),
                                                                                                       bytes_to_human(
                                                                                                           total_store_size,
                                                                                                           'g'),
                                                                                                       bytes_to_human(
                                                                                                           total_store_size,
                                                                                                           't')))

        count_discrepancy = False
        size_discrepancy = False

        if not total_db_files == total_store_files:
            count_discrepancy = True

        if not total_db_size == total_store_size:
            size_discrepancy = True

        if size_discrepancy or count_discrepancy:
            print("\n*** WARNING ***")

        if size_discrepancy:
            print(
                "There is a discrepancy between the size of files in the database ({:,d}) and the file store ({:,d})! Delta: {:,d} bytes".format(
                    total_db_size, total_store_size, total_db_size - total_store_size))

        if count_discrepancy:
            print(
                "There is a discrepancy between the number of files in the database ({:,d}) and the file store ({:,d})! Delta: {:,d}".format(
                    total_db_files, total_store_files, total_db_files - total_store_files))

        if size_discrepancy or count_discrepancy:
            print("**It is recommended to use the --verify switch to correct this.")
        else:
            print("Database and file store appear to be in sync!\n\n")


def main():
    parser = argparse.ArgumentParser(
        description="""File manager that can import files,
                        export file sets based on a list of hashes, export files NOT in a list, etc.""", epilog="""
                        This program can be used to manage files of any type. Before use, adjust the value of
                        'extensions' at the top of the file. Only files having an extension in this set will be
                        imported. A list of files that weren't imported will be documented in a log file when
                        the import operation finishes.
                        """)

    parser.add_argument("--base_directory", help="""The root directory where files
                                                will live. This is also where the database of file info will
                                                be created. Enclose directories with spaces in double quotes.
                                                This should be the first argument provided.
                                                """)

    parser.add_argument("--print_stats", choices=['lite', 'full'], help="""'lite' will produce statistics from
    information in the database only. 'full' will look at both the database and file store.
        """)

    parser.add_argument("--verify", action="store_true", help="""Perform consistency check.
     Stage 1 is verifying what is in the database against what is in the file store.
     Stage 2 is verifying what is in the file store against the database.
     When comparison is complete, the results are displayed and, if any issues are found,
     options presented to correct any inconsistencies.
            """)

    import_group = parser.add_argument_group('Import options', 'These options determine how files are imported')
    import_group.add_argument(
        "--import_from", help="""List of comma separated directories to import
                                files from. Enclose directories with spaces in double quotes. Directories should
                                NOT have trailing slashes (i.e. C:\\foo is OK, but C:\\bar\\ is NOT OK
                                """, metavar='PATHS_TO_IMPORT_FROM')
    import_group.add_argument(
        "--delete_existing", choices=['yes', 'simulate'], help="""When importing, delete source files if
                                                        they already exist in file store. If set to 'simulate' files
                                                         will not actually be deleted. This is useful to see what
                                                         would happen as a result of using this flag without actually
                                                         deleting files.
                                                        """)

    import_group.add_argument(
        "--delete_empty_directories", choices=['yes', 'simulate'], help="""When importing, delete any empty directories found.
                                                        If set to 'simulate' directories will not actually be deleted.
                                                        """)

    import_group.add_argument("--copy_new_destination", help="""The directory to copy any newly imported files into.
                                                    No renaming of files (except when conflicts exist) will be done.
                                                    If directory name has spaces, enclose it in double quotes
                                                    """, metavar='PATH_TO_DIRECTORY')

    generate_group = parser.add_argument_group('Generate hash list options',
                                               'These options determine how hash lists are generated')

    generate_group.add_argument("--generate_hash_list", help="""Creates a CSV file of all hashes in the database. Also
                                                    includes the relative path to the file. The file will be saved to
                                                    the file manager's base directory
                                                    """, choices=['all', 'ed2k', 'md4', 'md5', 'sha1b16', 'sha1b32'])

    generate_group.add_argument("--suppress_file_info", help="""When true, prevents relative file path and file size
                                                    from being included in the hash list. This is handy to generate
                                                    hash lists to import into X-Ways Forensics, etc.
                                                    """, action="store_true")

    export_group = parser.add_argument_group('Export options',
                                             'These options allow for exporting files in several ways.')

    # because crazy people may try to do both at once...
    export_group_exclusive = export_group.add_mutually_exclusive_group()

    export_group_exclusive.add_argument("--export_existing", help="""Export a copy of files in PATH_TO_TEXT_FILE to
                                                    --export_directory. The first line of the file should
                                                    be the hash type to query: md5, sha1b16, sha1b32, ed2k, or md4,
                                                    followed by one hash per line. Enclose paths with spaces
                                                    in double quotes.
                                                    """, metavar='PATH_TO_TEXT_FILE')

    export_group_exclusive.add_argument("--export_delta", help="""Export a copy of files
                                    NOT in PATH_TO_TEXT_FILE to --export_directory. The first line of the file should
                                                    be the hash type to query: md5, sha1b16, sha1b32, ed2k, or md4,
                                                    followed by one hash per line. Enclose paths with spaces
                                                    in double quotes.
                                                    This is useful to synchronize two different file manager instances
                                                    by 1) using --generate_hash_list on one instance and then 2)
                                                    using this option on the file from step 1. The resultant files
                                                    can then be imported into the instance from step 1.
                                                    """, metavar='PATH_TO_TEXT_FILE')

    export_group.add_argument("--export_directory", help="""The target directory when using --export_files_in_list or
                                                    --export_files_not_in_list options. Enclose directories with spaces
                                                    in double quotes.
                                                    """, metavar='PATH_TO_DIRECTORY')

    export_group.add_argument("--rename", help="""When true, all exported files will be renamed to match
                                                    the hash type from the provided file listing.
                                                    """, action="store_true")

    export_group.add_argument("--zip", help="""When true, all exported files will be added to a zip
                                                    archive in --export_directory.
                                                    """, action="store_true")


    # this stores our application parameters so it can get passed around to functions

    args = parser.parse_args()
    config = parse_config()
    appconfig = ApplicationConfiguration(config, args)


    x = args.delete_existing if args.delete_existing is None else False

    # if args.delete_existing:
    #     appconfig.delete_existing = args.delete_existing
    #
    # if args.delete_empty_directories:
    #     appconfig.delete_empty_directories = args.delete_empty_directories
    #
    # if args.copy_new_destination:
    #     appconfig.copy_new_destination = args.copy_new_destination

    # if args.base_directory:
    #     appconfig.base_directory = args.base_directory
    #     setup_base_directory(appconfig.base_directory)

    print('\n\n')

    init_db(appconfig)

    # Process things in a sane order so things later down the list of options are as complete as possible

    if args.verify:
        verify(appconfig)

    if args.import_from:  # since at least something was passed to this argument, lets try to import
        if extensions.intersection(auto_delete_extensions):
            print(
                "Cannot import files as there is at least one extension in common between 'extensions' and 'auto_delete_extensions: {}".format(
                    ", ".join(extensions.intersection(auto_delete_extensions))))
        else:
            directories = args.import_from.split(",")
            import_files(appconfig, directories)

    if args.generate_hash_list:
        (files_processed, hash_path) = generate_hash_list(appconfig, args.generate_hash_list, args.suppress_file_info)
        if files_processed:
            print("\n\nHashes for {} files have been exported to '{}'\n".format(files_processed, hash_path))
        else:
            print("\n\nNothing to export! The database is empty!\n")

    if args.export_existing or args.export_delta:
        if args.export_directory:
            appconfig.export_directory = os.path.normpath(args.export_directory)

            print("\tExport directory set to: {}".format(appconfig.export_directory))

            if not os.path.exists(appconfig.export_directory):
                print("\tExport directory does not exist. Creating...")
                os.makedirs(appconfig.export_directory)

            if args.rename:
                appconfig.rename_exported = True

            if args.zip:
                appconfig.zip_exported = True

            file_name = ""

            if args.export_existing:
                file_name = args.export_existing

            elif args.export_delta:
                file_name = args.export_delta

            if os.path.isfile(file_name):
                export_files(appconfig, bool(args.export_existing), file_name)
            else:
                print("\t{} does not exist! Export cancelled!".format(file_name))

        else:
            print("\t--export_directory must be set when exporting files! Export cancelled.")

            #see whats set in appconfig
            #attrs = vars(appconfig)
            #print('\n'.join("%s: %s" % item for item in attrs.items()))

            # TODO have a built in web mode to allow searching, exporting etc?
            # TODO Add error handling/try catch, etc
            # TODO make backup of SQLite DB on startup (if newer than last)
            # TODO add --purge_files that takes a list of files and cleans file store and DB of those hashes

    if args.print_stats:
        dump_stats(appconfig, args.print_stats)

    if not args.export_delta and not args.export_existing and not args.generate_hash_list and not args.import_from and not args.print_stats and not args.verify:
        print("You didn't ask me to do anything, so here are some statistics:")
        dump_stats(appconfig, 'lite')


def parse_config():
    config = configparser.ConfigParser()
    config.read('config.ini')

    # Check for required sections.

    if 'General' not in config:
        gen_sec_msg = 'Invalid format for config.ini. Missing "[{0}]" section.'
        fatal_error(gen_sec_msg.format('General'))

    # Check for required keys.

    if 'database_name' not in config['General']:
        gen_key_msg = 'Invalid format for config.ini. Missing key "{0}" under "[{1}]" section.'
        fatal_error(gen_key_msg.format('database_name', 'General'))

    if 'base_directory' not in config['General']:
        gen_key_msg = 'Invalid format for config.ini. Missing key "{0}" under "[{1}]" section.'
        fatal_error(gen_key_msg.format('base_directory', 'General'))

    # Check for invalid values

    if not config['General']['database_name']:
        gen_val_msg = 'Invalid format for config.ini. Invalid value for "{1}" key under "[{2}]" section.'
        fatal_error(gen_val_msg.format('database_name', 'General'))

    return config


def fatal_error(msg='Unknown'):
    print('\033[91m A fatal error has occurred: {0}\033[0m'.format(msg))
    print('\033[93m The program will now exit.\033[0m')
    exit(1)


if __name__ == '__main__':
    main()
