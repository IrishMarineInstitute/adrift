FROM opendrift/opendrift

MAINTAINER fullergalway@gmail.com

RUN apt-get update && \
     apt-get install -y python3-netcdf4 \
                        libssl-dev \
                        libffi-dev

COPY requirements.txt requirements.txt

RUN pip3 install Cython
RUN pip3 install -r requirements.txt

RUN mkdir /output && mkdir /input

COPY webapp /webapp
WORKDIR /webapp
EXPOSE 5000
CMD ["python3","app.py"]


