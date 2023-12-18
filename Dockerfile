FROM opendrift/opendrift

MAINTAINER fullergalway@gmail.com

RUN conda install -c conda-forge uwsgi

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

