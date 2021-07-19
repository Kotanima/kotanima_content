#!/bin/bash


# * * * * * bash /home/kotanima_project/kotanima_content/cron_scrape.sh >> /home/ubuntu/kotanima_scraper/scrape_log.txt 2>&1

source /home/kotanima_project/kotanima_content/.venv/bin/activate
cd /home/kotanima_project/kotanima_content
python src/downloader.py
