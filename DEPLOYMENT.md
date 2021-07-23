# Install postgres

`sudo apt update`

`sudo apt install postgresql postgresql-contrib`

2. Edit config file:

https://stackoverflow.com/a/26735105/10692354

after that:

`sudo service postgresql restart`

3. create and restore db with new user

```
psql -U postgres
CREATE DATABASE db_name;
```

# Recover database

Download db from yadisk to local computer

1. login to yadisk
2. find latest backup
3. Download it
4. Copy file to server:

```
scp /home/user/Downloads/db.backup.gz  root@00.111.222.33:/home/
```

5. Go to home directory and Unzip file

```
gunzip db.backup.gz
```

6. Restore from file

```
pg_restore -d db_name -U postgres db.backup
```

# Install pyenv

https://github.com/pyenv/pyenv/

```
pyenv install 3.9.x
```

# Install poetry

`curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python3 `

https://github.com/python-poetry/poetry

# Clone projects

```
cd /home/
```

```
mkdir kotanima_project
```

```
cd kotanima_project
```

```
git clone git@github.com:B0und/kotanima_server.git
```

```
git clone git@github.com:B0und/kotanima_content.git
```

cd into each folder and

```
pyenv local 3.9.X
```

```
poetry install
```

```
poetry config virtualenvs.in-project true
```

Check if its actually set to true:

```
poetry config --list
```

# clone mal-id-cache into kotanima_project

```
git clone https://github.com/seanbreckenridge/mal-id-cache.git
```

# copy .env file to kotanima_project

```
scp /home/user/Downloads/.env root@00.111.222.33:/home/kotanima_project/
```


Env file example:

```
STATIC_FOLDER_PATH=

# VK settings

VK_KROTKADZIMA_OWNER_ID=
VK_KOTANIMA_OWNER_ID=
VK_ACCESS_TOKEN=


# Database settings

DB_USER_NAME=
DB_USER_PASSWORD=
DB_PORT=
DB_NAME=

# Yandex settings

YANDEX_OAUTH_TOKEN=

# Gallery-dl pixiv refresh-token
GALLERY_DL_REFRESH_TOKEN=

# REDDIT PRAW SETTINGS

REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=
REDDIT_USERNAME=
REDDIT_PASSWORD=

# DJANGO SETTINGS
DJANGO_SECRET_KEY=

```

# test if kotanima server is working

```
cd kotanima_server
```

```
poetry run python manage.py runserver 0.0.0.0:8000
```

# go to kotanima_content

fill in info in backup.sh

# add cronjobs

Make sure that info in `backup.sh` is correct

```
crontab -e
```

add at the end:

```
00 05 * * * bash /home/kotanima_project/kotanima_content/sh_scripts/cron_scrape.sh >> /home/kotanima_project/scrape_log.txt 2>&1
*/2 * * * * bash /home/kotanima_project/kotanima_content/sh_scripts/cron_downloader.sh >>  /home/kotanima_project/downloader_log.txt 2>&1
00 06 */2 * * bash /home/kotanima_project/kotanima_content/sh_scripts/cron_vk_scheduler.sh >> /home/kotanima_project/scheduler_log.txt 2>&1
0 */2 * * * bash /home/kotanima_project/kotanima_content/sh_scripts/cron_metadata.sh >> /home/kotanima_project/metadata_log.txt 2>&1


```

probably need to create txt files manually


# Install and configure nginx

```
sudo apt install nginx
```

Wtf is nginx guide:

https://mattsegal.dev/nginx-django-reverse-proxy-config.html

Setup guide:

https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-18-04

# add SSL cert

https://www.digitalocean.com/community/tutorials/how-to-create-a-self-signed-ssl-certificate-for-nginx-in-ubuntu-18-04

sudo openssl req -x509 -nodes -days 730 -newkey rsa:2048 -keyout /etc/ssl/private/nginx-selfsigned.key -out /etc/ssl/certs/nginx-selfsigned.crt

actually good nginx config:

https://stackoverflow.com/questions/42244338/nginx-how-to-get-an-ssl-certificate-for-a-django-app
https://www.digitalocean.com/community/questions/http-https-redirect-positive-ssl-on-nginx

there should be 2 server{} blocks
one for SSL
one for redirect to SSL

Requests.get() now needs a public key file

https://stackoverflow.com/questions/30405867/how-to-get-python-requests-to-trust-a-self-signed-ssl-certificate
For reference (possibly for my future self), I had to download the certicicate as a .pem file by clicking on the lock icon in Firefox > Show Connection details > More information > View certificate > Download "PEM (chain)". The (chain) is the important part that I was missing as the alternative "PEM (cert)" will not work with requests. – Gaëtan de Menten Jan 15 at 9:28
