
# 0 */2 * * * bash /home/kotanima_project/kotanima_content/cron_metadata.sh >> /home/ubuntu/kotanima_scraper/metadata_log.txt 2>&1
source /home/kotanima_project/kotanima_content/.venv/bin/activate
cd /home/kotanima_project/kotanima_content
python src/add_metadata.py