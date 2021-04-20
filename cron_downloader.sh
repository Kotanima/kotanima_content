#!/bin/bash

PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/home/kotanima_project/kotanima_content/
cd /home/kotanima_project/kotanima_content
source $(poetry env info --path)/bin/activate
python src/downloader.py
