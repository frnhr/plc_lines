# PLC Lines

A Django app which reads a value from PLC devices over the network and detects when the connection 
is down of when the value is not what is expected.

These changes are logged in the database. 

A chart of daily uptime percentage is available for viewing and download as PDF.


## Disclaimer

This was a test assignment. I have zero experience with PLC devices, and obviously I don't have
one to test with, so I can only hope that the actual communication works.

I hope I didn't get the wrong assigment by mistake...  o_O

### Fake PLC Reader

To circumvent the fact that this assignment requires a rather specific piece of hardware,
a "FakeReader" was developed.

This is a module which can be loaded in place of the actual PLCReader module, and which
uses a simple JSON file to read from.

This fake reader is active by default, via this setting:
```
PLC_READER_CLASS = "devices.readers.FakeReader"
```   

To activate the real PLC reader module, replace that settings with:
```
PLC_READER_CLASS = "devices.readers.PLCReader"
```

## Setup and run

### Mac
```
brew install Caskroom/cask/wkhtmltopdf
pyenv virtualenv 3.8.1 plc_lines
pyenv local plc_lines
pip install -U pip poetry
poetry install

bin/celery &
./manage.py runserver
```

### Docker

```
docker-compose build

docker-compose up
```

### Production

NO!

The provided docker-compose setup is not production ready. 


## Initial data

Docker setup will automatically install some test data.

To do this manually, run `./manage.py init_db_and_data`.

A superuser is created with username `admin` and password `admin`.

To log in, open http://localhost:8000 


## PLC Lines Chart

To see the chart, go to http://localhost:8000/devices 

Change the date range and / or deselect some PLC devices, then click "Draw" to update the chart.

Clock "PDF" to download the cart as a PDF.


## Utility scripts

There is a number of utility scripts found in `bin` directory:

 * `bin/lint` - runs flake8 lint tool 
 * `bin/format` - runs black formatter
 * `bin/cover` - runs unit tests and shows coverage report
 * `bin/celery` - runs a Celery worker and beat process, only for development!
 * `bin/start-server` - runs Django web server via Gunicorn, used as default Docker command. 

## Assumptions

 * number of PLC devices is going to be "low"


## Design Decisions

### The admin

Most obvious design decision has been to use `django.contrib.admin` as the base for the whole UI.
I am assuming that the most important part of the assignment was backend code, so using
django-admin is a shortcut to spend less time coding UI and free up the time for more interesting
tasks.

### Chart library: D3

A few JS libraries were tested for charts:
 * [Apexcharts.js](https://apexcharts.com)
    - my first choice
 * [Chart.js](https://www.chartjs.org)
    - second choice
 * [D3](https://d3js.org)
    - final choice 
     
The choice came down to compatibility with pdfkit's HTML to PDF renderer.

Apexchart provides instructions for hot to export charts to PDF, but they rely on a paid library, 
and a ludicrously expensive one at that (https://www.fusioncharts.com/buy).  

### Using an iframe for the chart

For simplicity, I decided to show the chart in an iframe rather then building an API for the data.
The chart renders very quickly, so any speed gains that could be made by using an API are probably
below human detection. Moreover, initial load of the chart is faster since there is no second
HTTP request needed to fetch the data, it is already embedded in the response.

Using an iframe also simplified PDF exporting, since all the data is found in the URL of the iframe
and no additional steps are needed.

### Showing daily uptime average on the chart

The specs don't really say what should be shown on the charts, so I think this is the meaningful 
useful data.

### Underscore-plc_lines

My personal convention is to make the main project directory name start with an underscore. 
This distinguished it from other directories which are mostly django apps, and always keeps
it on top of alphabetical list. No other effects, just a convenience decision. 


## Incomprehensible specs

### Lines

> The manager should be able to choose the line, period machine from which wants to get the chart.

It is not clear what is a "line, period machine".

I am interpreting this as showing one line on a chart for every PLC device.

## E-mail

> Charts should be sent by email or generated PDF based on them.

Not really cleat at what conditions should an email be send. I'm skipping email altogether, 
since it would be somewhat difficult to set up for testing (need an actual SMTP account vs. 
it-just-runs in Docker).

## Reflection

With more information about exact use case, this project has the potential to be transformed into
a production-ready useful web app. 
 
## TODO / Ideas

 - [ ] Add options for uptime granularity
        * Currently uptime is always calculated on day-by-day basis.
        * If date range is sufficiently small, it makes sense to use hour as the base for uptime 
          calculation
        * Conversely, if the range is sufficiently large, is might make sense to use week of month
          as the base of calculation.
 - [ ] Improve support for greater number of PLC devices on the chart
        * ... and/or limit the number of devices on the chart.
        * Currently the labels in legend will tilt to accommodate more then 5 lines.
 - [ ] Daemonize Celery properly
        * Celery beat should be a service.
        * Maybe workers, too.
 - [ ] Make use of Redis for cache.
        * Not really using cache (explicitly) at the moment.
        * Configure `CACHES` to use Redis.
        * Be sure to set a prefix to avoid conflicts with Celery broker (but don't
          use multiple databases).   