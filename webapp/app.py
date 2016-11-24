from __future__ import print_function
from flask import Flask, render_template, jsonify, request, abort, send_file, redirect
from flask_socketio import SocketIO, emit
import glob
import netCDF4
import numpy as np
import dateutil.parser
import datetime
import pystache
import hashlib
import json
import codecs
import subprocess
import sys
import os
from processify import processify
import subprocess
import shutil
from operator import itemgetter

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

def _models():
  with open("models.json") as f:
    return json.load(f)

@app.route('/project/<path:project>/', methods=["DELETE"])
def delete_project(project):
    context = {}
    release_dir = "/output/{0}".format(project)
    with open("{0}/context.json".format(release_dir)) as f:
      context = json.load(f)
    if context["release_dir"] == release_dir:
       shutil.rmtree(release_dir)
    return "OK"
      

@app.route('/project/<path:project>/project')
def show_output(project):
    with open("/output/{0}/context.json".format(project)) as f:
      context = json.load(f)
      return render_template('project.html',latitude=context["latitude"],longitude=context["longitude"])

@app.route('/project/<path:project>/<file>')
def show_project_file(project,file):
    return send_file("/output/{0}/{1}".format(project,file))

@app.route('/project/new', methods=['GET','POST'])
def show_new():
    model = request.values.get('model','undefined')
    if model == 'undefined':
      return redirect("/")
    metadata = _models()
    if not model in metadata:
      return redirect("/")
    info = metadata[model]
    (time_min,time_max,lat_min,lat_max,lon_min,lon_max) = _range(model)
    return render_template('new.html',
             model=model,
             latitude=info["defaults"]["latitude"],
             latitude_min = lat_min,
             latitude_max = lat_max,
             longitude_min = lon_min,
             longitude_max = lon_max,
             date_min = time_min,
             date_max = time_max,
             longitude=info["defaults"]["longitude"])

@app.route('/project/<path:project>/')
def show_status(project):
    return render_template('status.html')

@app.route('/api/models')
def models():
  items = []
  for key, v in _models().iteritems():
     del v["defaults"]
     items.append(v)
  return jsonify(items)

def _range(model):
  pattern = '/input/{0}/*.nc'.format(model)
  fnames = glob.glob(pattern)
  fnames.sort()
  if len(fnames) == 0:
     print("no files found matching {0}".format(pattern), file=sys.stderr)
     abort(412)
  cdfa = netCDF4.MFDataset(fnames[0])
  cdfz = netCDF4.MFDataset(fnames[-1])
  start_time = netCDF4.num2date(cdfa.variables['ocean_time'][:],cdfa.variables['ocean_time'].units)[0]
  end_time = netCDF4.num2date(cdfz.variables['ocean_time'][:],cdfz.variables['ocean_time'].units)[0]
  
  time_min = "{0}Z".format(start_time).replace(" ","T")
  time_max = "{0}Z".format(end_time).replace(" ","T")
  lat_min = np.min(cdfa.variables['lat_u'][:])
  lat_max = np.max(cdfa.variables['lat_u'][:])
  lon_min = np.min(cdfa.variables['lon_u'][:])
  lon_max = np.max(cdfa.variables['lon_u'][:])
  return (time_min,time_max,lat_min,lat_max,lon_min,lon_max)

@app.route('/api/projects')
def list_projects():
  projects = []
  fnames = glob.glob("/output/*/*/*/*/context.json")
  for fname in fnames:
     with open(fname) as f:
       projects.append(json.load(f))
  projects = sorted(projects, key=itemgetter('created_time'), reverse=True)
  return jsonify(projects)

@app.route('/api/model/<model>/info')
def info(model):
  (time_min,time_max,lat_min,lat_max,lon_min,lon_max) = _range(model)
  return jsonify( time_min=time_min,
             time_max=time_max,
             lat_min=lat_min,
             lat_max=lat_max,
             lon_min=lon_min,
             lon_max=lon_max )

@app.route('/api/model/<model>/projection', methods=["GET","POST"])
def projection(model):
  metadata = _models()
  if not model in metadata:
    abort(404)
  defaults = metadata[model]["defaults"]

  (time_min,time_max,lat_min,lat_max,lon_min,lon_max) = _range(model)
  to_hash = {
    "model": {"time_min": time_min, "time_max": time_max, "lat_min": lat_min,
             "lat_max": lat_max, "lon_min": lon_min, "lon_max": lon_max
             }
  }
  project_name = request.values.get('project_name')
  start_release_time = dateutil.parser.parse(request.values.get('start_time',time_min))
  end_release_time = dateutil.parser.parse(request.values.get('end_release_time',start_release_time.isoformat()))
  end_time = dateutil.parser.parse(request.values.get('end_time',time_max))
  latitude = float(request.values.get('latitude',defaults["latitude"]))
  longitude = float(request.values.get('longitude',defaults["longitude"]))
  number_of_particles = int(request.values.get('number_of_particles','1000'))
  radius = float(request.values.get('radius','250'))
  depth = float(request.values.get('depth','0'))
  #Set the beginning date and time of the simulation. Format: year #### month ## day ## at HH:mm.
  beginning = start_release_time.strftime("year %Y month %m day %d at %H:%M.")
  #Set the duration of particle transport. Format: #### day(s) ## hour(s) ## minute(s)
  duration = end_time-end_release_time
  dhours, rem = divmod(duration.seconds,3600)
  dminutes, dseconds = divmod(rem,60)
  duration = "{0:0>4} day(s) {1:0>2} hour(s) {2:0>2} minute(s)".format(duration.days,dhours,dminutes)
  input_path = '/input/{0}'.format(model)
  model_date_path = '{0}/{1}'.format(model,datetime.datetime.today().strftime('%Y/%m'))
  output_path = '/output/{0}'.format(model_date_path)
  if not os.path.exists(output_path):
    os.makedirs(output_path)
  context = {
           'latitude': latitude,
           'longitude': longitude,
           'beginning': beginning,
           'duration': duration,
           'input_path': input_path,
           'output_path': output_path,
           'number_of_particles': number_of_particles,
           'depth': depth,
           'radius': radius,
           'model': model
   }
  to_hash["context"] = context
  hash = hashlib.sha224(json.dumps(to_hash,sort_keys=True)).hexdigest()
  output_file_prefix = "{0}_{1}".format(model,hash)
  release_dir = "{0}/{1}".format(output_path,hash)

  if os.path.exists(release_dir):
    # all ready to go.
    return redirect("{0}/".format(release_dir.replace("output","project",1)))

  #
  # First time this dataset was requested.
  # Start the generating process now.
  # Redirect the user to the project while it is still generating.
  #
  os.makedirs(release_dir)
  
  with open("{0}/status.json".format(release_dir),'w') as f:
    json.dump("preparing project",f)

  context['output_file_prefix'] =  output_file_prefix
  context['release_dir'] =  release_dir
  context['start_time'] = "{0}Z".format(start_release_time.isoformat())
  context['end_time'] = "{0}Z".format(end_time.isoformat())
  context['project_path'] = '/project/{0}/{1}/'.format(model_date_path,hash)
  context['created_time'] = "{0}Z".format(datetime.datetime.now().isoformat()[0:19])
  context['project_name'] = project_name
  context_file_path = "{0}/context.json".format(release_dir)
  with open(context_file_path,'w') as f:
    json.dump(context,f)

  generate_project(context_file_path)
  return redirect("{0}/".format(release_dir.replace("output","project",1)))

def overwrite_json_file(path,contents):
     with open("{0}.next".format(path),'w') as f:
         json.dump(contents,f)
     os.rename("{0}.next".format(path),path)

@processify
def generate_project(context_file_path):
   context = None
   with open(context_file_path) as f:
     context = json.load(f)
   status_output_path = "{0}/status.json".format(context["release_dir"])
   log_output_path = "{0}/log.txt".format(context["release_dir"])
   try:
     _generate_project(context,status_output_path,log_output_path)
   except:
     overwrite_json_file(status_output_path,"Project failed: {0}".format(sys.exc_info()[0]))

def _generate_project(context,status_output_path,log_output_path):
  release_dir = context["release_dir"]
  output_path = context["output_path"]
  output_file_prefix = context["output_file_prefix"]
  model = context["model"]

  json_output_path = "{0}/timepoints.json".format(release_dir)
  geojson_output_path = "{0}/geo.json".format(release_dir)
  times_output_path = "{0}/times.json".format(release_dir)
  js_output_path = "{0}/projection.js".format(release_dir)
  nc_output_path = "{0}/output.nc".format(release_dir)

  point_output_path = "{0}/point_{1}.json".format(release_dir,"{0}")

  overwrite_json_file(status_output_path,"start processing")

  if not os.path.isfile(nc_output_path):
    nc_output_pattern = '{0}/{1}*.nc'.format(output_path,output_file_prefix)
    fnames = glob.glob(nc_output_pattern)
    if len(fnames) == 0:
      xmlconfig = '{0}/{1}.xml'.format(output_path,output_file_prefix)
      encoding = 'cp1252';
      xml = None
      with codecs.open('{0}.xml.mustache'.format(model), encoding = encoding) as myfile:
        xml = myfile.read()
        xml = pystache.render(xml,context)

      with codecs.open(xmlconfig,'w',encoding) as myfile:
        myfile.write(xml)
  
      with open(log_output_path,'w') as applog:
        proc = subprocess.Popen(['java', '-jar', '/ichthyop/ichthyop-3.2.jar', xmlconfig], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in iter(proc.stdout.readline, ''):
          applog.write(line)
          if line.startswith("INFO: Step"):
            overwrite_json_file(status_output_path,line)

      fnames = glob.glob(nc_output_pattern)
  
    fnames.sort()
    os.rename(fnames[0],nc_output_path)

  overwrite_json_file(status_output_path,"extracting data from the generated file")
  (points,points2) = extract_points(nc_output_path) 
  times = []
  for point in points2:
    times.append(point["timestamp"])
    target = point_output_path.format(point["timestamp"])
    overwrite_json_file(status_output_path,"writing points for {0}".format(point["timestamp"]))
    with open(target,'w') as f:
      json.dump(point["points"],f)

  overwrite_json_file(status_output_path,"writing timestamps")
  with open(times_output_path,'w') as f:
      json.dump(times,f)

  overwrite_json_file(status_output_path,"writing geo.json")
  with open(geojson_output_path,'w') as myfile:
    json.dump(points,myfile)

  overwrite_json_file(status_output_path,"writing timepoints.json")
  with open(json_output_path,'w') as myfile:
    json.dump(points2,myfile)

  overwrite_json_file(status_output_path,"writing projection.js")
  with open(js_output_path,'w') as f:
    f.write("projection=");
    json.dump(points,f)
    f.write(";\n");

  overwrite_json_file(status_output_path,"Finished")


def extract_points(url):
  nc = netCDF4.Dataset(url)

  t = nc.variables['time'][:]
  time_origin = nc.variables['time'].origin
  time_units = 'seconds since 1968-05-23T00:00:00Z'
  time_calendar = nc.variables['time'].calendar

  map = None
  results = []
  times = []
  for i in range(len(t)):
    time = netCDF4.num2date(t[i],units=time_units,calendar=time_calendar)
    timestamp = "{0}Z".format(time.isoformat())
    points = {"timestamp": timestamp, "points": []}
    times.append(points)
    result = {"time": timestamp, "features": []}
    lat = nc.variables['lat'][:]
    lon = nc.variables['lon'][:]
    for j in range(len(lon[i])):
      points["points"].append([float(lat[i][j]),float(lon[i][j])]);
      feature = {"type": "Feature", "geometry":{
             "time": timestamp,
             "type": "Point", "coordinates": [ float(lat[i][j]), float(lon[i][j])]
                   }}
      #result["features"].append(feature)
      results.append(feature)
    # results.append(result)
  return (results,times)


@socketio.on('my event')
def test_message(message):
    emit('my response', {'data': 'got it!'})

if __name__ == '__main__':
    socketio.run(app,host='0.0.0.0')
