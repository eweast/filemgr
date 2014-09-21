import os
import settings
import configparser
from util.fatal_error import fatal_error


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


def configure_settings(config, args):
    settings.database_name = config['General']['database_name']
    settings.base_directory = os.path.abspath(args.base_directory or config['General']['base_directory'] or '')
    settings.database_file = os.path.join(settings.base_directory, settings.database_name)
    settings.delete_existing = args.delete_existing if args.delete_existing is not None else False
    settings.copy_new_destination = args.copy_new_destination if args.copy_new_destination is not None else ''
    settings.export_directory = ''
    settings.rename_exported = False
    settings.zip_exported = False
    settings.delete_empty_directories = args.delete_empty_directories if args.delete_empty_directories is not None \
        else False

    if args.export_existing or args.export_delta:
        if args.export_directory:
            settings.export_directory = os.path.normpath(args.export_directory)

            print("\tExport directory set to: {}".format(settings.export_directory))

            if not os.path.exists(settings.export_directory):
                print("\tExport directory does not exist. Creating...")
                os.makedirs(settings.export_directory)

            if args.rename:
                settings.rename_exported = True

            if args.zip:
                settings.zip_exported = True

            file_name = ""

            if args.export_existing:
                file_name = args.export_existing

            elif args.export_delta:
                file_name = args.export_delta

            from ops.export_files import export_files
            if os.path.isfile(file_name):
                export_files(bool(args.export_existing), file_name)
            else:
                print("\t{} does not exist! Export cancelled!".format(file_name))

        else:
            print("\t--export_directory must be set when exporting files! Export cancelled.")

            #see whats set in appconfig
            #attrs = vars(appconfig)
            #print('\n'.join("%s: %s" % item for item in attrs.items()))


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
