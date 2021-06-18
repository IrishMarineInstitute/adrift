# adrift
Project for connecting java-based particle transport models to modern web visualisations

![](adrift.gif)

# Overview

Adrift provides a web frontend for [OpenDrift](https://opendrift.github.io) giving a way for less technical
users to generate model output and visualisations once the hard work has been done by the oceanographer.

The action is performed by accepting a small number of inputs from the user (location, start time, duration, radius, object type),
which are merged into an OpenDrift python template template at runtime.

The output is available for display in the web browser, and for download as netcdf.

The Norwegian Meteorological Institute have also created Web based API interface for running Opendrift simulations called “Drifty” ( https://rest.drifty.met.no/ )

# How to Run ADRIFT yourself

## Quick Start

 1. git clone this project
 ```bash
 git clone -b opendrift https://github.com/irishmarineinstitute/adrift adrift-opendrift
 ```
 2. Build the project. This will take a while the first time.
 ```bash
 cd adrift-opendrift
 docker build -t adrift-opendrift . 
 ```
 3. start the docker container
 ```bash
 docker run --rm -p 5000:5000 adrift-opendrift
 ```
 4. connect with your browser to [http://localhost:5000/](http://localhost:5000)

 ## Full configuration

To use ADRIFT with your own models, some further configuration is required before doing the docker build. In particular you will need to modify models.json file in the webapps folder.

# Configuration

Before installation, the models available for production are listed in [models.json](adrift/blob/master/webapp/models.json).
Depending on your model type and the source of input data, three modes of operation are available

## models.json format
The format for models.json is an object keyed by the model id.
Example:
```json
  "connemara_his": {
    "id": "connemara_his",
    "name": "Connemara",
    "opendap_url": "http://thredds.marine.ie/thredds/dodsC/connemara_native/connemara_native_aggregate.nc",
    "wind_url": "http://thredds.marine.ie/thredds/dodsC/adrift_wind/adrift_wind_aggregate.nc",
    "defaults": {
      "latitude": 53.256302,
      "longitude": -9.005189,
      "northwest_lat": 52,
      "northwest_lon": -10,
      "southeast_lat": 50,
      "southeast_lon": -8
    },
    "leeway_drifters": ["PIW-1", "PIW-6", "LIFE-RAFT-DB-10", "PERSON-POWERED-VESSEL-1", "PERSON-POWERED-VESSEL-2", "PERSON-POWERED-VESSEL-3", "FISHING-VESSEL-1", "SAILBOAT-1", "SAILBOAT-2", "OIL-DRUM", "CONTAINER-1", "SLDMB"],
    "variables": {
      "latitude": "lat_u",
      "longitude": "lon_u",
      "time": "ocean_time"
    }
  }
``` 
<dl>
  <dt>id</dt>
  <dd>A short code id for the model; this must be the same as the key used to identify the model (connemara_his in the above example).</dd>

  <dt>name</dt>
  <dd>The display name for the model; this will appear in the dropdown list on the main page</dd>
  
  <dt>opendap_url</dt>
  <dd>Required when the model is held in an from opendap server. In the examples provided, the opendap_url is used in both the cmems_ibi and NEATL models.</dd>

  <dt>defaults</dt>
  <dd>This section provides default parameters used for display and processing</dd>

  <dt>defaults.latitude</dt>
  <dd>Initial marker placement latitude.</dd>

  <dt>defaults.longitude</dt>
  <dd>Initial marker placement longitude</dd>

  <dt>defaults.northwest_lat</dt>
  <dd>Northwest corner</dd>

  <dt>defaults.northwest_lon</dt>
  <dd>Northwest corner</dd>

  <dt>defaults.southeast_lat</dt>
  <dd>Southeast corner</dd>

  <dt>defaults.southeast_lon</dt>
  <dd>Southeast corner</dd>

  <dt>leeway_drifters</dt>
  <dd>A list of the preferred OpenDrift Leeway object_types</dd>

  <dt>variables</dt>
  <dd>This section tells ADRIFT how to read the latitude longitude and time from the netcdf files or opendap connection.</dd>

  <dt>variables.latitude</dt>
  <dd>Name of the latitude variable/dimension</dd>

  <dt>variables.longitude</dt>
  <dd>Name of the longitude variable/dimension</dd>

  <dt>variables.time</dt>
  <dd>Name of the time variable/dimension</dd>
  
</dl>

# For Developers

The section below is for developers changing any of the mustache templates or implementing other
functionality:

## Mustache templates

The following placeholders are available:

<dl>
<dt>{{beginning}}</dt>
<dd>Use for value of the the initial_time parameter</dd>

<dt>{{depth}}</dt>
<dd>Use for value of the depth_stain parameter. Note there is no way for the user to change this value of this parameter at present.</dd>

<dt>{{duration}}</dt>
<dd>Use for value of the transport_duration parameter</dd>

<dt>{{input_path}}</dt>
<dd>Use for the value of the input_path parameter where the input files are on the local filesystem</dd>

<dt>{{latitude}}</dt>
<dd>Use for the value of the lat_stain parameter</dd>

<dt>{{longitude}}</dt>
<dd>Use for the value of the lon_stain parameter</dd>

<dt>{{opendap_url}}</dt>
<dd>The URL of the opendap aggregate; Use for the value of the opendap_url parameter.</dd>

<dt>{{output_path}}</dt>
<dd>Use for the value of the output_path parameter in the main output section</dd>

<dt>{{radius}}</dt>
<dd>Use for the value of the radius_stain parameter</dd>



# installation

```bash
docker build -t adrift-opendrift .
```

## Saving output

To save the output folder, consider using a docker mount. For example:
```bash
docker run -d --restart=always --name=adrift-opendrift -v /path/to/saved/output:/output -p 5000:5000 adrift-opendrift
```

## Running in Docker Swarm

```bash
docker build -t 127.0.0.1:5000/adrift-opendrift .
docker push 127.0.0.1:5000/adrift-opendrift
```

Running in docker-compose also check the docs to create the [htaccess password file](https://github.com/jwilder/nginx-proxy#basic-authentication-support)


### example docker swarm
```docker service create --name adrift-opendrift --label traefik.port=5000 --label traefik.domain=dm.marine.ie --network traefik-net --mount type=bind,src=/data/gfs/adrift-opendrift/output,dst=/output 127.0.0.1:5000/adrift-opendrift:latest ```

