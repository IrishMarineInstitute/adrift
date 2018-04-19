# adrift
Project for connecting java-based particle transport models to modern web visualisations

# installation
Before installing, download [ichthyop-3.2.zip](http://www.ichthyop.org/) into the folder.

# nfs mount
Connect ROMS output to the host server.

1. Install the autofs package if it’s not already installed
2. put the attached auto.prometheus file in the /etc folder
3. add the following line to the /etc/auto.master file (which should exist if autofs is installed)
  * ```/mnt/prometheus /etc/auto.prometheus --ghost --timeout=60 --verbose```
4. create new folder: /mnt/prometheus
5. restart autofs: /etc/init.d/autofs restart

```bash
docker build -t adrift .
```

# running

```bash
docker run -d --restart=always \
-v /mnt/prometheus/shared/model/ROMS/OUTPUT/Connemara/FC/WEEK_ARCHIVE/:/input/connemara_his \
-v /home/opsuser/dev/docker-ichthyop/output:/output \
-p 80:5000 --name=adrift adrift
```

Running in docker-compose also check the docs to create the [htaccess password file](https://github.com/jwilder/nginx-proxy#basic-authentication-support)

