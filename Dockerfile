FROM openjdk:6
RUN apt-get update
RUN apt-get install -y build-essential git python-pip python-numpy python-dev
COPY install_netcdf4.sh install_netcdf4.sh
RUN ./install_netcdf4.sh
RUN pip install netCDF4 --upgrade
RUN pip install flask-socketio gevent
RUN apt-get install -y python-dateutil
RUN pip install pystache
COPY ichthyop-3.2.zip ichthyop-3.2.zip 
RUN unzip ichthyop-3.2.zip
RUN rm -f ichthyop-*.zip && mv ichthyop* ichthyop
RUN mkdir /output && mkdir /input
COPY webapp /webapp
WORKDIR /webapp
CMD ["python","app.py"]


