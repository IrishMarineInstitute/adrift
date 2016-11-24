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
RUN curl -o- https://deb.nodesource.com/setup_4.x | sed -e 's/https/http/g' | bash -
RUN apt-get install -y nodejs
RUN npm install phantomjs-prebuilt

# RUN apt-get update && \
# apt-get -y install autoconf automake build-essential libass-dev libfreetype6-dev libgpac-dev \
#    libsdl1.2-dev libtheora-dev libtool libva-dev libvdpau-dev libvorbis-dev libx11-dev \
#    libxext-dev libxfixes-dev pkg-config texi2html zlib1g-dev \
#    wget unzip yasm libx264-dev libmp3lame-dev libopus-dev && \
#    mkdir ~/ffmpeg_sources
#
# Build ffmpeg
#RUN cd ~/ffmpeg_sources && \
#    wget http://ffmpeg.org/releases/ffmpeg-snapshot.tar.bz2 && \
#    tar xjvf ffmpeg-snapshot.tar.bz2 && \
#    cd ffmpeg && \
#    PATH="$HOME/bin:$PATH" PKG_CONFIG_PATH="$HOME/ffmpeg_build/lib/pkgconfig" ./configure \
#    --prefix="$HOME/ffmpeg_build" \
#    --extra-cflags="-I$HOME/ffmpeg_build/include" \
#    --extra-ldflags="-L$HOME/ffmpeg_build/lib" \
#    --bindir="$HOME/bin" \
#    --enable-gpl \
#    --enable-libass \
#    --enable-libfreetype \
#    --enable-libmp3lame \
#    --enable-libopus \
#    --enable-libtheora \
#    --enable-libvorbis \
#    --enable-libx264 \
#    --enable-nonfree \
#    --enable-x11grab && \
#    PATH="$HOME/bin:$PATH" make && \
#    make install && \
#    make distclean && \
#    hash -r

COPY webapp /webapp
WORKDIR /webapp
CMD ["python","app.py"]


