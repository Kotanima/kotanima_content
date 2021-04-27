import yadisk
import os
import glob
import pathlib
from subprocess import Popen
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())


################################################################################################
# PATH VARIABLES, CAN CHANGE OR CREATE THESE EXACT FOLDERS (keep structure!!):
django_backup_path = r"./Backups/"
backup_bat_path = r"."  # backup.sh script location 

################################################################################################
django_backup_path = str(pathlib.Path(django_backup_path).absolute())
backup_bat_path = str(pathlib.Path(backup_bat_path).absolute())


def get_latest_postgres_dump_path(backup_path):
    list_of_files = glob.glob(backup_path + '/*')
    latest_file = max(list_of_files, key=os.path.getctime)
    return latest_file


def run_dumps():

    if not os.path.exists(django_backup_path):
        os.makedirs(django_backup_path)

    with Popen("./backup.sh", cwd=backup_bat_path) as p:
        p.communicate()


def start_upload_to_yandex():
    oauth_token = os.environ.get("YANDEX_OAUTH_TOKEN")
    y = yadisk.YaDisk(token=oauth_token)

    postgres_p = pathlib.Path(get_latest_postgres_dump_path(django_backup_path))
    y.upload(str(postgres_p),
             f"/new_django/{postgres_p.name}", overwrite=True, timeout=300)


def main():
    run_dumps()
    start_upload_to_yandex()


if __name__ == "__main__":
    main()
