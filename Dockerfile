FROM python:3.8-buster

RUN apt-get update && apt-get install -y --no-install-recommends \
    vim wkhtmltopdf nodejs npm postgresql-client
RUN mkdir -p /opt/app
WORKDIR /opt/app
RUN npm install npm@latest -g
RUN pip install -U pip poetry && \
    poetry config virtualenvs.create false
COPY . /opt/app/
RUN poetry install

EXPOSE 8000
STOPSIGNAL SIGTERM
CMD ["/opt/app/bin/start-server"]
