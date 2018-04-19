FROM openjdk:6
RUN apt-get update
RUN apt-get install -y build-essential git python-pip python-numpy python-dev
COPY install_netcdf4.sh install_netcdf4.sh
RUN ./install_netcdf4.sh
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
# You'll need to fetch ichthyop from http://www.ichthyop.org/downloads
COPY ichthyop-3.2.zip ichthyop-3.2.zip 
RUN unzip ichthyop-3.2.zip
RUN rm -f ichthyop-*.zip && mv ichthyop* ichthyop
RUN mkdir /output && mkdir /input

COPY webapp /webapp
WORKDIR /webapp
CMD ["python","app.py"]


