
import initialize
from fs.queries import *
from ops.import_files import import_files
from ops.verify import verify
from cli.arguments import parse_arguments
from initialize import parse_config
from util.byte_conversion import bytes_to


# TODO use pathlib vs os.path calls? this is 3.4 only
# http://docs.sqlalchemy.org/en/rel_0_9/orm/tutorial.html ??
# http://docs.python.org/3.4/howto/logging-cookbook.html

# logger = logging.getLogger('filemgr')
# logger.setLevel(logging.CRITICAL)
# fh = logging.FileHandler('filemgr_debug.log')
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# fh.setFormatter(formatter)
# logger.addHandler(fh)

# def generate_missing_hashes(file):
# """ Given file, look for missing hashes, generate them, and update the
#     database """
#
#     return "not done yet"


def dump_stats(print_stats):
    print("\n*** Database statistics ***\n")

    if print_stats == 'full':
        print("\t *** Please be patient while file store statistics are calculated. This may take a while! ***\n")

    (total_db_files, total_db_size, total_store_files, total_store_size) = get_stats(print_stats)

    print("Total files in database: {:,d}".format(total_db_files))
    print("Total size of files in database: {:,d} bytes ({:,f} MB, {:,f} GB, {:,f} TB)\n".format(total_db_size,
                                                                                                 bytes_to(
                                                                                                     total_db_size,
                                                                                                     'm'),
                                                                                                 bytes_to(
                                                                                                     total_db_size,
                                                                                                     'g'),
                                                                                                 bytes_to(
                                                                                                     total_db_size,
                                                                                                     't')))

    if print_stats == 'full':
        print("Total files in file store: {:,d}".format(total_store_files))
        print("Total size of files in file store: {:,d} bytes ({:,f} MB, {:,f} GB, {:,f} TB)\n".format(total_store_size,
                                                                                                       bytes_to(
                                                                                                           total_store_size,
                                                                                                           'm'),
                                                                                                       bytes_to(
                                                                                                           total_store_size,
                                                                                                           'g'),
                                                                                                       bytes_to(
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

    args = parse_arguments()
    config = parse_config()
    initialize.configure_settings(config, args)
    initialize.setup_base_directory(settings.base_directory)
    print('\n\n')

    init_db()

    # Process things in a sane order so things later down the list of options are as complete as possible

    if args.verify:
        verify()

    if args.import_from:  # since at least something was passed to this argument, lets try to import
        if settings.extensions.intersection(settings.auto_delete_extensions):
            print(
                "Cannot import files as there is at least one extension in common between 'extensions' and "
                "'auto_delete_extensions: {}".format(", ".join(settings.extensions.intersection(settings.auto_delete_extensions))))
        else:
            directories = args.import_from.split(",")
            import_files(directories)

    if args.generate_hash_list:
        (files_processed, hash_path) = generate_hash_list(args.generate_hash_list, args.suppress_file_info)
        if files_processed:
            print("\n\nHashes for {} files have been exported to '{}'\n".format(files_processed, hash_path))
        else:
            print("\n\nNothing to export! The database is empty!\n")

    if args.print_stats:
        dump_stats(args.print_stats)

    if not args.export_delta and not args.export_existing and not args.generate_hash_list and not args.import_from and not args.print_stats and not args.verify:
        print("You didn't ask me to do anything, so here are some statistics:")
        dump_stats('lite')

    # TODO have a built in web mode to allow searching, exporting etc?
    # TODO Add error handling/try catch, etc
    # TODO make backup of SQLite DB on startup (if newer than last)
    # TODO add --purge_files that takes a list of files and cleans file store and DB of those hashes


if __name__ == '__main__':
    main()
