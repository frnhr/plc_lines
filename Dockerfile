FROM python:3.8-buster

RUN apt-get update && apt-get install -y --no-install-recommends \
    vim wkhtmltopdf nodejs npm postgresql-client
RUN npm install npm@latest -g
RUN pip install -U pip poetry && \
    poetry config virtualenvs.create false
RUN mkdir -p /opt/app
COPY . /opt/app/
WORKDIR /opt/app
RUN poetry install && \
    npm -v && \
    npm i && \
    python manage.py collectstatic --clear --noinput

EXPOSE 8000
STOPSIGNAL SIGTERM
CMD ["/opt/app/bin/start-server"]
