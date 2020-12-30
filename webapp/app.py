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
import sys
import os
from processify import processify
import subprocess
import shutil
from operator import itemgetter
import traceback
from opendrift.models.leeway import Leeway
from opendrift.readers import reader_netCDF_CF_generic
import math

os.environ["HDF5_USE_FILE_LOCKING"] = "FALSE"

LEEWAY_OBJECTS = []
def _init():
  global LEEWAY_OBJECTS
  l = Leeway()
  LEEWAY_OBJECTS = [{
    'OBJKEY': l.leewayprop[item]['OBJKEY'],
    'Description': l.leewayprop[item]['Description'] 
    }
            for i,item in enumerate(l.leewayprop)]

_init()

app = Flask(__name__)
socketio = SocketIO(app)


@app.route('/')
def index():
    models = sorted([model for key, model in _models().items()],
            key=lambda x: x['name'])
    return render_template('index.html', models=models)

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

@app.route('/project/<path:project>/update', methods=['POST'])
def update_context(project):
    context = None
    context_file_path = "/output/{0}/context.json".format(project)
    with open(context_file_path) as f:
      context = json.load(f)
    name = request.values.get('name')
    if "ctx_" in name:
       name = name[4:]
    value = request.values.get('value')
    if name in context:
       context[name] = value
       with open(context_file_path,'w') as f:
          json.dump(context,f)
    return "OK"

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
    (time_min,time_max,lat_min,lat_max,lon_min,lon_max,polygon) = _range(model)
    return render_template('new.html',
             model=model,
             latitude=info["defaults"]["latitude"],
             latitude_min = lat_min,
             latitude_max = lat_max,
             longitude_min = lon_min,
             longitude_max = lon_max,
             date_min = time_min,
             date_max = time_max,
             longitude=info["defaults"]["longitude"],
             shrink_domain=info["shrink_domain"],
             polygon=json.dumps([list(p) for p in polygon]))

@app.route('/project/<path:project>/')
def show_status(project):
    return render_template('status.html')

def list_leeway_objects():
  return [{"index": i+1,
            "key": o["OBJKEY"],
            "label": "{0} {1}".format(o["OBJKEY"],o["Description"])} 
            for i,o in enumerate(LEEWAY_OBJECTS)]

@app.route('/api/models')
def models():
  items = []
  for key, v in _models().iteritems():
     del v["defaults"]
     items.append(v)
  return jsonify(items)

def _get_times(cdf,var_time):
  units = cdf.variables[var_time].units
  times = [netCDF4.num2date(t,units) for t in cdf.variables[var_time]]
  return ["{0}Z".format(t).replace(" ","T") for t in times]

def _range(model):
  md = _models()[model]
  var_time = md['variables']['time']
  var_lat = md['variables']['latitude']
  var_lon = md['variables']['longitude']
  if "opendap_url" in md:
    cdfa = netCDF4.Dataset(md["opendap_url"])
    cdfz = cdfa
  else:
    pattern = '/input/{0}/*.nc'.format(model)
    fnames = glob.glob(pattern)
    fnames.sort()
    if len(fnames) == 0:
       print("no files found matching {0}".format(pattern), file=sys.stderr)
       abort(412)
    cdfa = netCDF4.Dataset(fnames[0])
    cdfz = netCDF4.Dataset(fnames[-1])

  if "wind_url" in md:
    cdfx = netCDF4.Dataset(md["wind_url"])
    return _getrange(cdfx,cdfx,'time','lat','lon')

  return _getrange(cdfa,cdfz,var_time,var_lat,var_lon)

def _getrange(cdfa,cdfz,var_time,var_lat,var_lon):

  time_min = _get_times(cdfa,var_time)[0]
  time_max = _get_times(cdfz,var_time)[-1]

  # TODO: fix these to work also on 2d model...
  lat_min = float(cdfa.variables[var_lat][:][:].min())
  lat_max = float(cdfa.variables[var_lat][:][:].max())
  lon_min = float(cdfa.variables[var_lon][:][:].min())
  lon_max = float(cdfa.variables[var_lon][:][:].max())
  try:
    lat1 = lat2 = cdfa.variables[var_lat][0].item()
    lon1 = lon4 = cdfa.variables[var_lon][0].item()
    lat3 = lat4 = cdfa.variables[var_lat][-1].item()
    lon2 = lon3 = cdfa.variables[var_lon][-1].item()
  except ValueError:
    lat1 = cdfa.variables[var_lat][0][0].item()
    lat2 = cdfa.variables[var_lat][0][-1].item()
    lat3 = cdfa.variables[var_lat][-1][-1].item()
    lat4 = cdfa.variables[var_lat][-1][0].item()
    lon1 = cdfa.variables[var_lon][0][0].item()
    lon2 = cdfa.variables[var_lon][0][-1].item()
    lon3 = cdfa.variables[var_lon][-1][-1].item()
    lon4 = cdfa.variables[var_lon][-1][0].item()

  polygon = [[lat1,lon1],[lat2,lon2],[lat3,lon3],[lat4,lon4]]
  return (time_min,time_max,lat_min,lat_max,lon_min,lon_max,polygon)

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
  (time_min,time_max,lat_min,lat_max,lon_min,lon_max,polygon) = _range(model)
  leeway_drifters = ["PIW-1", "PIW-6", "LIFE-RAFT-DB-10", "PERSON-POWERED-VESSEL-1", "PERSON-POWERED-VESSEL-2", "PERSON-POWERED-VESSEL-3", "FISHING-VESSEL-1", "SAILBOAT-1", "SAILBOAT-2", "OIL-DRUM", "CONTAINER-1", "SLDMB"]
  if "leeway_drifters" in model:
    leeway_drifters = model["leeway_drifters"]
  leeway_objects = list_leeway_objects()
  for o in leeway_objects:
    if o["key"] in leeway_drifters:
       o["preferred"] = True

  return jsonify( time_min=time_min,
             time_max=time_max,
             lat_min=lat_min,
             lat_max=lat_max,
             lon_min=lon_min,
             lon_max=lon_max,
             polygon=polygon,
             leeway_drifters=leeway_objects)

def _indexOfLastNotGreater(l,val):
  l2 = [v for v in l if v<=val]
  if len(l2):
    return len(l2) - 1
  return 0

def _indexOfLastNotSmaller(l,val):
  l.reverse()
  l2 = [v for v in l if v>=val]
  answer = len(l)-1
  if len(l2):
    answer = len(l)-len(l2)
  l.reverse()
  return answer

def _calculate_nc_fetch_url(
          md, 
          start_time,
          end_time,
          northwest_lat,
          northwest_lon,
          southeast_lat,
          southeast_lon):
  """
  Replace the {lat_range} {lon_range} {time_range} params in a string
  Example:
  "nc_fetch_url": "http://thredds.marine.ie/thredds/dodsC/IMI_CMEMS/AGGREGATE?lon[{{lon_range}}],lat[{{lat_range}}],v[{{time_range}}][{{lat_range}}][{{lon_range}}],time[{{time_range}}],u[{{time_range}}][{{lat_range}}][{{lon_range}}]"
  """
  if not "opendap_url" in md:
    return "ERROR nc_fetch_url can only be used if opendap_url is provided in models.json"

  cdfa = netCDF4.Dataset(md["opendap_url"])
  print(cdfa, file=sys.stderr)
  var_lat = md['variables']['latitude']
  var_lon = md['variables']['longitude']
  var_time = md['variables']['time']
  nc_fetch_url_pattern = md["nc_fetch_url"]
  lats = [x.item() for x in cdfa.variables[var_lat]]
  lons = [x.item() for x in cdfa.variables[var_lon]]
  times = _get_times(cdfa,var_time)
  time_range = "{0}:1:{1}".format(_indexOfLastNotGreater(times,start_time),
                                  _indexOfLastNotSmaller(times,end_time))
  lat_range = "{0}:1:{1}".format(
      _indexOfLastNotSmaller(lats,southeast_lat),
      _indexOfLastNotGreater(lats,northwest_lat))

  lon_range = "{0}:1:{1}".format(_indexOfLastNotGreater(lons,northwest_lon),
                                  _indexOfLastNotSmaller(lons,southeast_lon))
  return pystache.render(nc_fetch_url_pattern,{
    "time_range": time_range,
    "lat_range": lat_range,
    "lon_range": lon_range
    })



@app.route('/api/model/<model>/projection', methods=["GET","POST"])
def projection(model):
  metadata = _models()
  if not model in metadata:
    abort(404)
  defaults = metadata[model]["defaults"]

  (time_min,time_max,lat_min,lat_max,lon_min,lon_max,polygon) = _range(model)
  to_hash = {
    "model": {"time_min": time_min, "time_max": time_max, "lat_min": lat_min,
             "lat_max": lat_max, "lon_min": lon_min, "lon_max": lon_max
             }
  }
  object_type = int(request.values.get('object_type','1'))
  leeway_object = LEEWAY_OBJECTS[object_type-1]
  object_type_description = leeway_object["Description"]
  object_type_key = leeway_object["OBJKEY"]
  start_release_time = dateutil.parser.parse(request.values.get('start_time',time_min))
  project_name = request.values.get('project_name',
                '{0} {1}'.format(start_release_time.strftime("%Y-%m-%d %H:%M"),object_type_key))
  end_release_time = dateutil.parser.parse(request.values.get('end_release_time',start_release_time.isoformat()))
  end_time = dateutil.parser.parse(request.values.get('end_time',time_max))
  latitude = float(request.values.get('latitude',defaults["latitude"]))
  longitude = float(request.values.get('longitude',defaults["longitude"]))
  number_of_particles = int(request.values.get('number_of_particles','1000'))
  radius = float(request.values.get('radius','250'))
  depth = float(request.values.get('depth','0'))
  northwest_lat = float(request.values.get('northwest_lat',defaults['northwest_lat']))
  northwest_lon = float(request.values.get('northwest_lon',defaults['northwest_lon']))
  southeast_lat = float(request.values.get('southeast_lat',defaults['southeast_lat']))
  southeast_lon = float(request.values.get('southeast_lon',defaults['southeast_lon']))
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
  updates = {
           'latitude': latitude,
           'longitude': longitude,
           'beginning': beginning,
           'duration': duration,
           'input_path': input_path,
           'output_path': output_path,
           'number_of_particles': number_of_particles,
           'depth': depth,
           'radius': radius,
           'model': model,
           'northwest_lat': northwest_lat,
           'northwest_lon': northwest_lon,
           'southeast_lat': southeast_lat,
           'southeast_lon': southeast_lon,
           'object_type': object_type,
           'object_type_key': object_type_key,
           'object_type_description': object_type_description,
           'drifter': '{0}. {1}: {2}'.format(object_type, object_type_key, object_type_description.replace('>',''))
   }
  context = {**defaults, **updates}
  for key in ["opendap_url", "shrink_domain"]:
      if key in metadata[model]:
          context[key] = metadata[model][key]

  to_hash["context"] = context
  hash = hashlib.sha224(json.dumps(to_hash,sort_keys=True).encode('utf-8')).hexdigest()
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
  context['start_time'] = start_release_time.isoformat()
  context['start_time_datetime'] = start_release_time.strftime("%Y,%-m,%-d,%-H,%-M")
  context['end_time'] = start_release_time.isoformat()
  context['end_time_datetime'] = end_time.strftime("%Y,%-m,%-d,%-H,%-M")
  context['project_path'] = '/project/{0}/{1}/'.format(model_date_path,hash)
  context['created_time'] = "{0}Z".format(datetime.datetime.now().isoformat()[0:19])
  context['project_name'] = project_name
  if "nc_fetch_url" in metadata[model]:
    context["nc_input_file"] = "{0}/input.nc".format(release_dir)
    context["nc_fetch_url"] =  _calculate_nc_fetch_url(
          metadata[model], 
          context['start_time'],
          context['end_time'],
          northwest_lat,
          northwest_lon,
          southeast_lat,
          southeast_lon)
  if "wind_url" in metadata[model]:
    context["wind_url"] = metadata[model]["wind_url"]

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
     traceback.print_exc(file=sys.stderr)
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
  context["nc_output_path"] = nc_output_path;

  point_output_path = "{0}/point_{1}.json".format(release_dir,"{0}")
  if("nc_fetch_url" in context):
    overwrite_json_file(status_output_path,"nccopy {0} {1}".format(context["nc_fetch_url"], context["nc_input_file"]))
    with open(log_output_path,'a') as applog:
      logline = "nccopy {0} {1}".format(context["nc_fetch_url"], context["nc_input_file"])
      overwrite_json_file(status_output_path,logline)
      applog.write(logline+"\n")
      proc = subprocess.Popen(['nccopy', context["nc_fetch_url"], context["nc_input_file"]],
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
      for line in iter(proc.stdout.readline, b''):
        line = line.decode('utf-8')
        applog.write(line)

  overwrite_json_file(status_output_path,"start processing")
  
  if not os.path.isfile(nc_output_path):
    nc_output_pattern = '{0}/{1}*.nc'.format(output_path,output_file_prefix)
    fnames = glob.glob(nc_output_pattern)
    if len(fnames) == 0:
      pyscript = '{0}/leeway.py'.format(release_dir)
      encoding = 'utf-8';
      pycode = None
      with codecs.open('leeway.py.mustache', encoding = encoding) as myfile:
        pycode = myfile.read()
        pycode = pystache.render(pycode,context)

      with codecs.open(pyscript,'w',encoding) as myfile:
        myfile.write(pycode)
  
      with open(log_output_path,'a') as applog:
        proc = subprocess.Popen(['python', pyscript],
          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in iter(proc.stdout.readline, b''):
          line = line.decode('utf-8')
          applog.write(line)
          overwrite_json_file(status_output_path,line)
        
        if "nc_input_file" in context:
          if os.path.exists(context["nc_input_file"]):
            applog.write("removing {0}\n".format(context["nc_input_file"]))
            os.remove(context["nc_input_file"])

      fnames = glob.glob(nc_output_pattern)
  
    #fnames.sort()
    #os.rename(fnames[0],nc_output_path)

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
  time_units = nc.variables['time'].units # 'seconds since 1970-01-01 00:00:00'
  time_calendar = 'gregorian'

  map = None
  results = []
  times = []
  for i in range(len(t)):
    time = netCDF4.num2date(t[i],units=time_units,calendar=time_calendar)
    # timestamp = "{0}Z".format(time.isoformat())
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    points = {"timestamp": timestamp, "points": []}
    times.append(points)
    result = {"time": timestamp, "features": []}
    lats = nc.variables['lat'][:]
    lons = nc.variables['lon'][:]
    for j in range(len(lons)):
      lamask = np.ma.getmaskarray(lats[j])
      lomask = np.ma.getmaskarray(lons[j])
      if lamask[i] or lomask[i]:
        continue
      lat = float(lats[j][i])
      lon = float(lons[j][i])
      points["points"].append([lat,lon]);
      feature = {"type": "Feature", "geometry":{
             "time": timestamp,
             "type": "Point", "coordinates": [lat,lon]
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
