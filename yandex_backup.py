import yadisk
import os
import glob
import pathlib
from subprocess import Popen
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())


################################################################################################
# PATH VARIABLES, CAN CHANGE OR CREATE THESE EXACT FOLDERS (keep structure!!):
path_to_backup_folder = r"./Backups/"
path_to_backup_script = r"./sh_scripts/"  # backup.sh script location 

################################################################################################
path_to_backup_folder = str(pathlib.Path(path_to_backup_folder).absolute())
path_to_backup_script = str(pathlib.Path(path_to_backup_script).absolute())


def get_latest_postgres_dump_path(backup_path):
    list_of_files = glob.glob(backup_path + '/*')
    latest_file = max(list_of_files, key=os.path.getctime)
    return latest_file


def run_dumps():

    if not os.path.exists(path_to_backup_folder):
        os.makedirs(path_to_backup_folder)

    with Popen("./backup.sh", cwd=path_to_backup_script) as p:
        p.communicate()


def start_upload_to_yandex():
    oauth_token = os.environ.get("YANDEX_OAUTH_TOKEN")
    y = yadisk.YaDisk(token=oauth_token)

    postgres_p = pathlib.Path(get_latest_postgres_dump_path(path_to_backup_folder))
    y.upload(str(postgres_p),
             f"/new_django/{postgres_p.name}", overwrite=True, timeout=300)


def main():
    run_dumps()
    start_upload_to_yandex()


if __name__ == "__main__":
    main()
