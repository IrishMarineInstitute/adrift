FROM python:3.11-slim

RUN apt-get update && apt-get install -y build-essential python3-dev gcc

RUN pip install opendrift uwsgi

COPY requirements.txt requirements.txt

RUN pip3 install Cython
RUN pip3 install -r requirements.txt

RUN useradd -ms /bin/bash uwsgi

RUN mkdir /output && mkdir /input

COPY webapp /webapp
RUN chown -R uwsgi:uwsgi /output /input /webapp

COPY __init__.py /code/opendrift/models/basemodel/

USER uwsgi
WORKDIR /webapp
EXPOSE 5000
CMD ["uwsgi", "--enable-threads", "--http", ":5000", "--wsgi-file", "wsgi.py"]

