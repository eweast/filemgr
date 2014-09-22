from cli.dump_stats import dump_stats
import initialize
from db.queries import *
from ops.import_files import import_files
from ops.verify import verify
from cli.arguments import parse_arguments
from initialize import parse_config


# todo use pathlib vs os.path calls? this is 3.4 only
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
# database """
#
#     return "not done yet"

def main():
    args = parse_arguments()
    config = parse_config()
    initialize.configure_settings(config, args)
    initialize.setup_base_directory(settings.base_directory)
    print('\n\n')

    init_db()

    # Process things in a sane order so things later down the list of options are as complete as possible

    if args.verify:
        verify()  # This appears to detect/correct issues between the fs and db.

    if args.import_from:  # since at least something was passed to this argument, lets try to import
        if settings.extensions.intersection(settings.auto_delete_extensions):
            print(
                "Cannot import files as there is at least one extension in common between 'extensions' and "
                "'auto_delete_extensions: {}".format(
                    ", ".join(settings.extensions.intersection(settings.auto_delete_extensions))))
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