#!/bin/bash

# 00 07 * * * bash /home/kotanima_project/kotanima_content/cron_vk_scheduler.sh >> /home/kotanima_project/scheduler_log.txt 2>&1

source /home/ubuntu/kotanima_project/kotanima_content/.venv/bin/activate
cd /home/ubuntu/kotanima_project/kotanima_content
python src/vk_scheduler.py
python src/vk_scheduler.py
python src/vk_scheduler.py
python src/vk_scheduler.py
python src/vk_scheduler.py
