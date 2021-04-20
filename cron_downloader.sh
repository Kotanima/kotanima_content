#!/bin/bash

cd /home/kotanima_project/kotanima_content
source $(poetry env info --path)/bin/activate
python src/downloader.py
