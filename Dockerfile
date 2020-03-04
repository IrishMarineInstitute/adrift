FROM openjdk:8
RUN apt-get update
RUN apt-get install -y build-essential git python3-dev python3-pip
RUN apt-get install -y libcurl4-openssl-dev
RUN apt-get install -y m4
RUN apt-get install -y file
COPY install_netcdf4.sh install_netcdf4.sh
RUN ./install_netcdf4.sh
RUN mv /include/* /usr/local/include/
RUN apt-get install -y libssl-dev libffi-dev
#RUN easy_install pip
COPY requirements.txt requirements.txt
RUN pip3 install Cython
RUN pip3 install -r requirements.txt
# You'll need to fetch ichthyop from http://www.ichthyop.org/downloads
# COPY ichthyop*.zip ichthyop.zip 
# Pinned to this version now for cmems_ibi
# http://www.ichthyop.org/system/files/downloads/ichthyop-v3u3.zip
COPY ichthyop-v3u3.zip ichthyop.zip
RUN unzip -d unzipped ichthyop.zip && \
    mv unzipped/* ichthyop && \
    rm -rf unzip ichthyop*.zip

RUN mkdir /output && mkdir /input

COPY webapp /webapp
WORKDIR /webapp
EXPOSE 5000
CMD ["python3","app.py"]


