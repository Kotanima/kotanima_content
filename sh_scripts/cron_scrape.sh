#!/bin/bash

# setup for cron job:
# crontab -e
# 00 06 * * * bash /home/kotanima_project/kotanima_content/cron_scrape.sh >> /home/ubuntu/kotanima_scraper/scrape_log.txt 2>&1


source /home/ubuntu/kotanima_project/kotanima_content/.venv/bin/activate
cd /home/ubuntu/kotanima_project/kotanima_content
python scrape_reddit.py praw_scrape --subreddit_name="patchuu" --amount=1000 --PRAW_MODE=PostSearchType.NEW
python scrape_reddit.py praw_scrape --subreddit_name="awenime" --amount=1000 --PRAW_MODE=PostSearchType.NEW
python scrape_reddit.py praw_scrape --subreddit_name="moescape" --amount=1000 --PRAW_MODE=PostSearchType.NEW
python scrape_reddit.py praw_scrape --subreddit_name="fantasymoe" --amount=1000 --PRAW_MODE=PostSearchType.NEW
python scrape_reddit.py praw_scrape --subreddit_name="awwnime" --amount=1000 --PRAW_MODE=PostSearchType.NEW
python scrape_reddit.py praw_scrape --subreddit_name="artistic_ecchi" --amount=1000 --PRAW_MODE=PostSearchType.NEW
#python scrape_reddit.py praw_scrape --subreddit_name="ecchi" --amount=1000 --PRAW_MODE=PostSearchType.NEW
python yandex_backup.py
