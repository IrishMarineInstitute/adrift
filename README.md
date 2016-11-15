# adrift
Project for connecting java-based particle transport models to modern web visualisations

# installation
Before installing, download [ichthyop-3.2.zip](http://www.ichthyop.org/) into the folder.

```bash
docker build -t adrift .
```

# running

```bash
docker run -d -v /opt/oceansql_data/CONNEMARA/:/input/connemara_his -p 80:5000 adrift
```

