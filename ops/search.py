from fs.get_fileinfo import get_fileinfo
from util.fatal_error import fatal_error
from db.queries import check_file_exists_in_database
import settings
import os


def search_file(filepath):
    print('Searching database for {0}'.format(filepath), end='\n\n')

    file_info = None
    try:
        file_info = get_fileinfo(filepath)
    except FileNotFoundError:
        fatal_error('Check file path; Unable to find file at {0}'.format())
    except PermissionError:
        fatal_error('Insufficient permissions to access {0}'.format(filepath))
    except BlockingIOError:
        fatal_error('Unable to access, another process has opened {0}'.format(filepath))

    row = check_file_exists_in_database(4, file_info['hashes']['sha1b32'])

    if row[0] is not '':
        print('\033[94mFile found! See {0}\033[0m'.format(os.path.join(settings.base_directory, row[0])))
        pass
    else:
        print('\033[94mFile not found in database.\033[0m')