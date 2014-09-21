

database_name = None
base_directory = None
database_file = None
delete_existing = None
copy_new_destination = None
export_directory = None
rename_exported = False
zip_exported = False
delete_empty_directories = None

# a list of valid file extensions to import. anything else will be skipped. make it a set in case people add dupes
extensions = {'.jpg', '.avi', '.ram', '.rm', '.wmv', '.pdf', '.mov', '.mp4', '.flv', '.jpe', '.jpeg', '.mpg', '.mpe',
              '.mpeg', '.png', '.3g2', '.3gp', '.asf', '.bmp', '.divx', '.gif', '.jpg', '.m1v', '.vob', '.mod', '.tif',
              '.mkv', '.jp2', '.psd', '.m4v', '.pcx'}

# a list of extensions to delete. If any of these extensions are found in 'extensions' the import will be cancelled
auto_delete_extensions = {'.db', '.com', '.scr', '.htm', '.html', '.url', '.thm', '.tmp', '.ds_store', '.ico', '.rtf',
                          '.doc', '.ini', '.ascii', '.dat', '.svg'}

BUFFER_SIZE = 65536  # 8192 # file reading buffer size 8192 * 64?