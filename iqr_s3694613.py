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
import numpy as np
from scipy.stats import iqr
from scipy.stats.mstats import mquantiles
from PyQt5.QtCore import QVariant
from PyQt5.QtCore import QCoreApplication
from qgis.utils import iface
from qgis.core import (QgsProcessing,
                        QgsProject,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                        QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterField,
                       QgsProcessingParameterFeatureSink)
import processing


class IQR(QgsProcessingAlgorithm):
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
        return IQR()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'IQR'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Find IQR and create new shapefile')

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
        return self.tr("Remove outliers of a specific field and create a new output file")

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        # We add the input vector features source. It can have any kind of
        # geometry.
        
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                name="INPUT",
                description="Input layer",
                types=[QgsProcessing.TypeVectorAnyGeometry]
            )
        )
        #add field from the input vector
        self.addParameter(
        QgsProcessingParameterField(
            name="req",
            description="Field (Must be numeric)",
            parentLayerParameterName="INPUT",
            type=QgsProcessingParameterField.Numeric
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

        # Retrieve the feature source and sink. 
        source = self.parameterAsSource(parameters,
                                        'INPUT',
                                        context)
        req = self.parameterAsSource(parameters,
                                        'req',
                                        context)
        
        #Initialise needed variables
        chosenFile = self.parameterDefinition('INPUT').valueAsPythonString(parameters['INPUT'], context)
        filePath = os.path.dirname(chosenFile[1:]) + '\\'
        feedback.pushInfo(filePath) 

        #4.2.Identify locations with extreme UHI (low or high)
        #4.2.1. IQR
        v0aLayer = iface.addVectorLayer((filePath + chosenFile), chosenFile[:-4],"ogr")
        v0aLayer = iface.activeLayer()
        features = v0aLayer.getFeatures()
        idx = v0aLayer.fields().indexFromName(req)
        l=[]
        for f in features:
            attrs = f.attributes()[idx]
            l.append(attrs)
        x = np.array(l)
        IQR= iqr(x)
        Q = mquantiles(x)
        firstQ = Q[0]
        thirdQ = Q[2]
        v0aLayer = iface.activeLayer()
        v0aLayer.startEditing()
        prov=v0aLayer.dataProvider()
        prov.addAttributes([QgsField("OUTLIER", QVariant.String)])
        v0aLayer.updateFields()
        v0aLayer.commitChanges()
        features = v0aLayer.getFeatures()
        for f in features:
            if f[req] > (thirdQ + IQR):
                outlier = "High"
            else:
                outlier = "No"
            v0aLayer.startEditing()
            f["OUTLIER"]= outlier
            v0aLayer.updateFeature(f)
            v0aLayer.commitChanges()
        #4.2.2. Remove high Outliers (where defenitely Urban vegetation does is low and 
        #UHI is explained by Land cover (built surfaces)
        v0alayer = iface.activeLayer()
        v0alayer.selectByExpression("\"OUTLIER\"='No'", QgsVectorLayer.SetSelection)
        selectDict = {'INPUT':(filePath + v0aFileName) ,\
                      'OUTPUT': (filePath + v3FileName)}
        processing.run("native:saveselectedfeatures", selectDict)
        
        return {self.OUTPUT}
