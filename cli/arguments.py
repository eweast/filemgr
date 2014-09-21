import argparse


def parse_arguments():
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
        "--delete_empty_directories", choices=['yes', 'simulate'], help="""When importing, delete any empty directories
                                                        found. If set to 'simulate' directories will not actually be
                                                        deleted.""")

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

    return parser.parse_args()