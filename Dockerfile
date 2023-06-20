FROM opendrift/opendrift

MAINTAINER fullergalway@gmail.com

RUN apt-get update && \
     apt-get install -y python3-netcdf4 \
                        libssl-dev \
                        libffi-dev

#RUN apt-get install -y build-essential
RUN conda install -c conda-forge uwsgi

COPY requirements.txt requirements.txt

RUN pip3 install Cython
RUN pip3 install -r requirements.txt

RUN useradd -ms /bin/bash uwsgi

RUN mkdir /output && mkdir /input

COPY webapp /webapp
RUN python3 /webapp/get_rid_of_spatial_coverage_error.py
RUN chown -R uwsgi:uwsgi /output /input /webapp

USER uwsgi
WORKDIR /webapp
EXPOSE 5000
CMD ["uwsgi", "--enable-threads", "--http", ":5000", "--wsgi-file", "wsgi.py"]

