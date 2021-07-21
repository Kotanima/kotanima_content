#!/bin/bash
# example useage:
# ./restore_db.sh 2021-07-16.backup
pg_restore --clean --if-exists  --host=localhost --port=5432 --username=postgres --no-owner --create --dbname=kaa_prod "$1"
