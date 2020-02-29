FROM python:3.8-buster

# install nginx
RUN apt-get update && apt-get install -y --no-install-recommends vim wkhtmltopdf

# copy source and install dependencies
RUN mkdir -p /opt/app
COPY . /opt/app/
WORKDIR /opt/app
RUN pip install -U pip poetry && \
    poetry config virtualenvs.create false && \
    poetry install

# start server
EXPOSE 8000
STOPSIGNAL SIGTERM
CMD ["/opt/app/bin/start-server"]
