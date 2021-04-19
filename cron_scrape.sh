#!/bin/bash

# setup for cron job:
# crontab -e
# 00 06 * * * bash /home/ubuntu/kotanima_scraper/cron_scrape.sh >> /home/ubuntu/kotanima_scraper/scrape_log.txt 2>&1

source /home/ubuntu/kotanima_scraper/env/bin/activate
cd /home/ubuntu/kotanima_scraper/
python /home/ubuntu/kotanima_scraper/yandex_backup.py
python /home/ubuntu/kotanima_scraper/scrape_reddit.py praw_scrape --subreddit_name="patchuu" --amount=1000 --PRAW_MODE=PostSearchType.NEW
python /home/ubuntu/kotanima_scraper/scrape_reddit.py praw_scrape --subreddit_name="awenime" --amount=1000 --PRAW_MODE=PostSearchType.NEW
python /home/ubuntu/kotanima_scraper/scrape_reddit.py praw_scrape --subreddit_name="moescape" --amount=1000 --PRAW_MODE=PostSearchType.NEW
python /home/ubuntu/kotanima_scraper/scrape_reddit.py praw_scrape --subreddit_name="fantasymoe" --amount=1000 --PRAW_MODE=PostSearchType.NEW
python /home/ubuntu/kotanima_scraper/scrape_reddit.py praw_scrape --subreddit_name="awwnime" --amount=1000 --PRAW_MODE=PostSearchType.NEW
python /home/ubuntu/kotanima_scraper/scrape_reddit.py praw_scrape --subreddit_name="artistic_ecchi" --amount=1000 --PRAW_MODE=PostSearchType.NEW
python /home/ubuntu/kotanima_scraper/scrape_reddit.py praw_scrape --subreddit_name="ecchi" --amount=1000 --PRAW_MODE=PostSearchType.HOT
python /home/ubuntu/kotanima_scraper/yandex_backup.py
