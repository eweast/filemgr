import os
import settings


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


