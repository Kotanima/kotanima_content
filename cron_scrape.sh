#!/bin/bash

# setup for cron job:
# crontab -e
# 00 06 * * * bash /home/ubuntu/kotanima_scraper/cron_scrape.sh >> /home/ubuntu/kotanima_scraper/scrape_log.txt 2>&1

cd /home/kotanima_project/kotanima_content/
poetry run python /home/kotanima_project/kotanima_content/yandex_backup.py
poetry run python /home/kotanima_project/kotanima_content/scrape_reddit.py praw_scrape --subreddit_name="patchuu" --amount=1000 --PRAW_MODE=PostSearchType.NEW
poetry run python /home/kotanima_project/kotanima_content/scrape_reddit.py praw_scrape --subreddit_name="awenime" --amount=1000 --PRAW_MODE=PostSearchType.NEW
poetry run python /home/kotanima_project/kotanima_content/scrape_reddit.py praw_scrape --subreddit_name="moescape" --amount=1000 --PRAW_MODE=PostSearchType.NEW
poetry run python /home/kotanima_project/kotanima_content/scrape_reddit.py praw_scrape --subreddit_name="fantasymoe" --amount=1000 --PRAW_MODE=PostSearchType.NEW
poetry run python /home/kotanima_project/kotanima_content/scrape_reddit.py praw_scrape --subreddit_name="awwnime" --amount=1000 --PRAW_MODE=PostSearchType.NEW
poetry run python /home/kotanima_project/kotanima_content/scrape_reddit.py praw_scrape --subreddit_name="artistic_ecchi" --amount=1000 --PRAW_MODE=PostSearchType.NEW
poetry run python /home/kotanima_project/kotanima_content/scrape_reddit.py praw_scrape --subreddit_name="ecchi" --amount=1000 --PRAW_MODE=PostSearchType.NEW
poetry run python /home/kotanima_project/kotanima_content/yandex_backup.py
