# adrift
Project for connecting java-based particle transport models to modern web visualisations

# installation
Before installing, download [ichthyop-3.3.3.zip](http://www.ichthyop.org/system/files/downloads/ichthyop_3.3.3_1.zip) into the folder.

NB: the current cmems_ibi configuration works only with an older version [Ichthyop 3.3_r1031](http://www.ichthyop.org/system/files/downloads/ichthyop-3.3.zip)

# nfs mount
Connect ROMS output to the host server.

1. Install the autofs package if it’s not already installed
2. put the attached auto.prometheus file in the /etc folder
3. add the following line to the /etc/auto.master file (which should exist if autofs is installed)
  * ```/mnt/prometheus /etc/auto.prometheus --ghost --timeout=60 --verbose```
4. create new folder: /mnt/prometheus
5. restart autofs: /etc/init.d/autofs restart

```bash
docker build -t 127.0.0.1:5000/adrift .
```

# fetching some model data data files from the main demo server
```bash
mkdir -p input/connemara_his
cd input/connemara_his
read username
read password
for item in 18 19 20 21 22 23 24 25; do wget --user=$username --password=$password "https://adrift.demo.marine.ie/nc/CONN_20180406${item}.nc"; done
```

# running

```bash
docker run -d --restart=always \
-v /mnt/prometheus/shared/model/ROMS/OUTPUT/Connemara/FC/WEEK_ARCHIVE/:/input/connemara_his \
-v /home/opsuser/dev/docker-ichthyop/output:/output \
-p 80:5000 --name=adrift adrift
```

Running in docker-compose also check the docs to create the [htaccess password file](https://github.com/jwilder/nginx-proxy#basic-authentication-support)


# docker swarm
```docker service create --name adrift --label traefik.port=5000 --label traefik.domain=dm.marine.ie --network traefik-net --mount type=bind,src=/opt/adrift/output,dst=/output --mount type=bind,src=/opt/thredds/connemara_his/,dst=/input/connemara_his --constraint node.hostname=="dmdock04" 127.0.0.1:5000/adrift:latest ```
