# -*- coding: utf-8 -*-

"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""
import os
from PyQt5.QtCore import QVariant
from PyQt5.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterDistance,
                       QgsProcessingParameterField,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterRange,
                       QgsProcessingParameterExpression,
                       QgsProcessingParameterFeatureSink)
import processing


class GWRegression(QgsProcessingAlgorithm):
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return GWRegression()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'gwregression'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Geographically Weighted Regression: A Method for Exploring Spatial Nonstationarity')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('Example scripts')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'examplescripts'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr("Performs Geographically Weighted Regression (GWR), \
        a local form of linear regression used to model spatially varying relationships. \
        Dependent variable: The numeric field containing values for what you are trying to model.\
        Explanatory variable(s): A list of fields representing independent explanatory \
        variables in your regression model.")

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It can have any kind of
        # geometry.
        self.addParameter(
            QgsProcessingParameterFeatureSource(
            name="InputLayer",
            description="Input Layer",
            types=[QgsProcessing.TypeVectorAnyGeometry] #QgsProcessing.SourceType.TypeVectorPoint
            #QgsProcessing.TypeVectorAnyGeometry
            )
        )
        self.addParameter(
        QgsProcessingParameterField(
            name="dependentVariable",
            description="Dependent variable",
            parentLayerParameterName="InputLayer",
            type=QgsProcessingParameterField.Numeric
            )
        )
        self.addParameter(
        QgsProcessingParameterField(
            name="explanatoryVariable",
            description="Explanatory variable(s)",
            parentLayerParameterName="InputLayer",
            allowMultiple=True,
            type=QgsProcessingParameterField.Numeric
            )
        )
        self.addParameter(
        QgsProcessingParameterExpression(
            name="sample",
            description="Sample size",
            defaultValue = '30',
            parentLayerParameterName="InputLayer"
            )
        )

        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Output layer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
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
        return {self.OUTPUT}
