# aqhi-website

A website collecting air quality data from [PM25.in](http://pm25.in/) and showing Air Quality Health Index(AQHI) based on the data collected.

The backend is developed with Python 3.5 using Django 1.9.5 on Ubuntu 15.04.

## Setup development environment, the shortest way

### Create a virtualenv and install python dependencies.

When this project was developed, some dependencies' need to be installed manually.

- First one is `drf-extensions`. 
Install the master branch version in its [repo](https://github.com/chibisov/drf-extensions).
- Second one is `lxml` if you are using Windows. 
Directly download binary file from [Python Extension Packages for Windows - Christoph Gohlke](http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml).

Once these two dependencies are installed, under the root directory of the project, install the rest:

```bash
workon project_venv
pip install -r requirements.txt
```

### Create .env file.

`.env` file defines required environment variables.

Sample file using production settings:

```
DJANGO_SETTINGS_MODULE=config.settings.production
DATABASE_URL=sqlite:////path/to/project/db.sqlite3
DJANGO_SECRET_KEY=hu*83623g@t8(6dt!et%v^jl$8=qgfo*zfk0*n+*0w_z=t!itj
DJANGO_ALLOWED_HOSTS=127.0.0.1
```

Sample file using development settings:

```
DJANGO_SETTINGS_MODULE=config.settings.local
DATABASE_URL=postgres://aqhi:aqhiweb@localhost:5432/aqhidb
```

Patterns of db url can be found [here](https://github.com/kennethreitz/dj-database-url#url-schema).

### Create database

Run:

```bash
python manage.py migrate
```

This will create sqlite3 database.

### Populate database with test data

- Populate `City` and `Station` model.

Firstly, crawl some web pages and save them in certain dir:

```bash
python manage.py start_crawl /path/to/saving/dir --not-parse
```

This will save pages under a subdirectory named with timestamp in the format of `YYYY-mm-dd-HH-MM-SS`.

Secondly, parse the crawled pages and get city and station names:

```bash
python manage.py collect_names /path/to/pages/dir
```

Lastly, create some sample coordinates data of cities and stations:

```bash
python mange.py add_coordinates city /path/to/project/aqhi/airquality/tests/files/sample_city_coords.txt
python mange.py add_coordinates city /path/to/project/aqhi/airquality/tests/files/sample_station_coords.txt
```

### Get real data

With the base of basic city and station data, we can finally crawl real data from the website and start developing:

```bash
python manage.py start_crawl /path/to/saving/dir
```

### Run server

If using production settings:

```bash
python manage.py collectstatic
python manage.py runserver --insecure
```

With development settings:

```bash
python manage.py runserver
```
