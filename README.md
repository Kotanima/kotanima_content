## Kotanima Project

The goal of this project is to (almost) automate content management for a VK group.


In short:
1. Images are downloaded from reddit, reddit title is parsed for tags, and comments are parsed for an image source link. This information is  stored in a PostgreSQL database.
2. Django REST API is used for database CRUD + nginx as reverse proxy and for serving static files
3. Kivy android application is used to rate images (like/dislike)
4. Liked images are grouped together and posted to VK.

## Table of contents

- [General info](#general-info)
- [Technologies](#technologies)
- [Deployment](#deployment)

## General info

This repository contains the main modules for

1. Downloading images from reddit, parsing title and comments to generate tags and find image source in the comments and adding them into the database.
2. Updating anime and characters database tables
3. Finding similar images for a VK post
4. VK scheduling of content. The images are postponed every hour until there are 100 postponed posts. (24 posts a day max ~= 4 days of content per vk_scheduler.py run)

## Technologies

Project is created with:

- Python 3
- `poetry` to manage dependencies
- `psycopg2` for interacting with a database (which in hindsight should have been an ORM, but this was still a good learning experience)
- `gallery-dl` for downloading images from multiple resources
- `praw`, `psaw` APIs for downloading data from reddit
- dozens of other cool libraries

## Deployment

Deployment is desciribed in detail [here](DEPLOYMENT.md)

## License

[MIT](LICENSE.md)