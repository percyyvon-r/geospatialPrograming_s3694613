import os
import numpy as np
from scipy.stats import iqr
from scipy.stats.mstats import mquantiles
from PyQt5.QtCore import QVariant
filePath = "D:\\fianarana\\RMIT_2018\\semester4\\geospatialProgramming\\module5_Poject\\file\\"
#VECTOR FILES
v0aFileName = "veg_grid.shp"
v0bFileName = "lga.shp"
v1FileName = "veg_uhi_grid_lga.shp"
v3FileName = "veg_grid_iqr.shp"
v4FileName = "centroid.shp"
v5FileName = "gwr.shp"

#RASTER FILES
r0FileName="uhi.tif"

#3.1.	Create vector file (table) that contains all variables and the LGA
#3.1.1.	Write import statements, set up local variables.
# Add the input layers to the map.
r0Layer = iface.addRasterLayer((filePath+r0FileName),r0FileName[:-4])
v0aLayer = iface.addVectorLayer((filePath+v0aFileName), v0aFileName[:-4],"ogr")

#3.1.2.	Use Zonal Statistics to calculate the mean of UHI per grid feature
zonalStatDict = {'INPUT_RASTER':(filePath + r0FileName) ,\
                 'RASTER_BAND':1,\
                 'INPUT_VECTOR': (filePath + v0aFileName),\
                 'COLUMN_PREFIX': "stat_",\
                 'STATS': 2}
processing.run("qgis:zonalstatistics", zonalStatDict)

#3.1.3.	Use join attribute by location to join the LGA layer to the grid layer. 
spatialJoinDict = {'INPUT':(filePath + v0aFileName) ,\
                   'JOIN': (filePath + v0bFileName),\
                   'PREDICATE':0,\
                   'JOIN_FIELDS':"" ,\
                   'METHOD' : 1,\
                   'DISCARD_NONMATCHING' : 2,\
                   'PREFIX': "",\
                   'OUTPUT': (filePath + v1FileName)}
processing.run("qgis:joinattributesbylocation", spatialJoinDict)
v1Layer = iface.addVectorLayer((filePath + v1FileName), v1FileName[:-4],"ogr")

#4.2.	Identify locations with high UHI
#4.2.1. IQR
v0aLayer = iface.activeLayer()
features = v0aLayer.getFeatures()
#extract the mean of UHI in one array
req="stat_mean"
idx = v0aLayer.fields().indexFromName(req)
l=[]
for f in features:
    attrs = f.attributes()[idx]
    l.append(attrs)
x = np.array(l)
#calculate IQR
IQR= iqr(x)
Q = mquantiles(x)
#first quantile
firstQ = Q[0]
#third quantile
thirdQ = Q[2]
v0aLayer = iface.activeLayer()
v0aLayer.startEditing()
prov=v0aLayer.dataProvider()
prov.addAttributes([QgsField("OUTLIER", QVariant.String)])
v0aLayer.updateFields()
v0aLayer.commitChanges()
features = v0aLayer.getFeatures()
for f in features:
    if f["stat_mean"] > (thirdQ + 1.5*IQR):
        outlier = "High"
    elif f["stat_mean"] > (thirdQ - 1.5*IQR):
        outlier = "Low"
    else:
        outlier = "No"
    v0aLayer.startEditing()
    f["OUTLIER"]= outlier
    v0aLayer.updateFeature(f)
    v0aLayer.commitChanges()

#4.2.2. Remove high Outliers (where defenitely Urban vegetation does is low and 
#UHI is explained by Land cover (high: built surfaces, low: vegetation)
v0alayer = iface.activeLayer()
v0alayer.selectByExpression("\"OUTLIER\"='No'", QgsVectorLayer.SetSelection)

selectDict = {'INPUT':(filePath + v0aFileName) ,\
              'OUTPUT': (filePath + v3FileName)}
processing.run("native:saveselectedfeatures", selectDict)
v3Layer = iface.addVectorLayer((filePath + v3FileName), v3FileName[:-4],"ogr")


#4.3. GWR using Tool GWR for Multiple Predictors
#From SAGA-GIS Tool Library Documentation (v6.1.0)
#4.3.1. Polygon centroids as input should be a point vector file
centroidDict = {'POLYGONS':(filePath + v3FileName) ,\
                'METHOD': 1,\
                'CENTROIDS': "ID",\
                'CENTROIDS': (filePath + v4FileName)}
processing.run("saga:polygoncentroids", centroidDict)
v4Layer = iface.addVectorLayer((filePath + v4FileName), v4FileName[:-4],"ogr")

#4.3.2. GWR
gwrDict = {'POINTS':(filePath + v4FileName) ,\
           'DEPENDENT': "stat_mean",\
            'PREDICTORS': "PLAND_ldsc, PD_ldscp, ED_ldscp",\
            'REGRESSION': (filePath + v5FileName),\
            'DW_WEIGHTING': 0,\
            'DW_IDW_POWER': 1,\
            'DW_IDW_OFFSET': 1,\
            'DW_BANDWIDTH': 0,\
            'SEARCH_RANGE' : 1,\
            'SEARCH_RADIUS': 1000,\
            'SEARCH_POINTS_ALL' : 1,\
            'SEARCH_POINTS_MIN' :30,\
            'SEARCH_POINTS_MAX' : 100,\
            'SEARCH_DIRECTION' : 0}
processing.run("saga:gwrformultiplepredictors", gwrDict)
v5Layer = iface.addVectorLayer((filePath + v5FileName), v5FileName[:-4],"ogr")
