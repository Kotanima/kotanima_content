#!/bin/bash

# 00 07 * * * bash /home/kotanima_project/kotanima_content/cron_vk_scheduler.sh >> /home/kotanima_project/scrape_log.txt 2>&1

source /home/kotanima_project/kotanima_content/.venv/bin/activate
cd /home/kotanima_project/kotanima_content
python src/vk_scheduler.py
