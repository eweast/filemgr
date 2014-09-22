from db.queries import get_stats
from util.byte_conversion import bytes_to


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