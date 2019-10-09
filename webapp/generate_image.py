import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import netCDF4
import numpy as np
from mpl_toolkits.basemap import Basemap

url = '/output/fred.nc'
nc = netCDF4.Dataset(url)

# examine the variables
print(nc.variables.keys())
t = nc.variables['time'][:]
depth = nc.variables['depth'][:]
region_edge = nc.variables['region_edge'][:]
mortality = nc.variables['mortality']
print(region_edge[4], region_edge[5])
print(nc.variables['time'])
print(t)

extent = [-9.75,-8.8,53.3,53.]
map = None
for i in range(len(t)):
  if i == 0:
    plt.figure(figsize=(10,10))
    map = Basemap(projection='merc',llcrnrlon=extent[0],llcrnrlat=extent[2],urcrnrlon=extent[1],urcrnrlat=extent[3],resolution='i') 
    map.drawcoastlines()
    # map.drawlsmask(land_color='Linen', ocean_color='#CCFFFF', resolution='f')
  lat = nc.variables['lat'][:]
  lon = nc.variables['lon'][:]
  # print lat
  # lons,lats= np.meshgrid(lon[i]-180,lat[i])
  # print lats
  # x,y = map(lons,lats)
  spot = map.scatter(lon[i],lat[i],marker='o',color='k',latlon=True,alpha=0.05)
  # plt.imshow([],extent=extent)
  plt.title("tada-{0}".format(i))
  plt.savefig('/output/image-{0}.png'.format(i), bbox_inches=0)
  spot.remove()
