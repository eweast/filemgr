from db.queries import *


def check_fs_to_db():
    bad_files = []

    db_file_names = get_files_from_db()

    for r, d, files in os.walk(os.path.join(settings.base_directory, "files")):
        for file in files:
            full_path = os.path.join(r, file)
            db_path = full_path.replace(settings.base_directory, "")
            db_path = db_path[1:]

            if not db_path in db_file_names:
                bad_files.append(full_path)
                print("\t{} is in file store but does not exist in database!".format(full_path))

    return bad_files
