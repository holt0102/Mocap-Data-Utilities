# -*- coding: utf-8 -*-

""" Este modulo consistira de funciones referentes 
    al manejo de datos de movimiento """
    
""" El tipo de archivos que manejará será .bvh"""

import bvh 
import geometry
import numpy as np

class Model( bvh.BVHReader ):
    """ A hierachical structure of nodes that contains the information
        of a 3D model and frames of its movement obtained from a bvh file
    """
    """ Attributes:
            numberOfFrames : The number of frames in the animation from the file
            frames : A list of the frames. Each frames has a list of values that takes each channel.
            frameTime : Indicates the sampling rate of the data.
            model_position : A dictionary that saves the global position in the current frame of a joint with its name as the key
            model_eulerAngles : A dictionary that saves the euler angles int the current frame of each joint with its name as the key
            model_edges : A list of all the edges between joints in the model in the order given by the a post order 
            model_frames_position : A list of dictionaries that saves the global position of each joint in every frame 

        Inherited Attributes:
            filename : Path to the file
            _root : A pointer to the root node of the Model
            _numchannels: The number of channels in the model
            nodeByName : A dictionary for accesing the model nodes by name
    """

    def __init__( self , filename ):
        """ Initializes the values of the attributes """
        bvh.BVHReader.__init__( self , filename )

        self.numberOfFrames = 0
        self.frames = []
        self.frameTime = 0 
    
        self.model_position = {}
        self.model_eulerAngles = {}
        self.model_edges = []

    def getJointByName( self , name ) :
        """ Returns a joint in the model by its name """
        return self.nodeByName[ name ]

    def onMotion( self , frames , dt ):
        """ Called when the 'MOTION' part of the .bvh is read.
            Set the frame values. """
        self.numberOfFrames = frames
        self.frameTime = dt

    def onFrame( self , values ):
        """ Called on every frame of the 'MOTION' section of the .bvh file.
            Add frame to frame list."""
        self.frames.append( values )     

    def setFrame( self , frame_index ):

        """ Calculate the positions of every joint in the 3D model in frame with number index. """
        
        self.channel_position = 0       ## Set index for traversing channels in frame
        self.model_edges = []           ## Reinitialize edges list
        self.getNodePosition( np.matrix(np.identity(4), copy=False ), self._root , self.frames[ frame_index ] )

    def getNodePosition( self , parent_transformation , current_node , frameChannels ):
        """ Recursive calculation of node position with transformation matrices """
        
        ## Initialize local transformation matrix
        current_node.transformation  = np.matrix( np.identity(4) , copy = False )
        current_node.rotation = np.matrix( np.identity(4) , copy = False )

        ## Initialize channel variables
        x_position , y_position , z_position = 0 , 0 , 0
        x_rotation , y_rotation , z_rotation = 0 , 0 , 0

        ## Obtain values for the channel variables
        for channel in current_node.channels:
            if( channel == "Xposition" ):
                x_position = frameChannels[ self.channel_position ]  

            elif( channel == "Yposition" ):
                y_position = frameChannels[ self.channel_position ]  

            elif( channel == "Zposition" ):
                z_position = frameChannels[ self.channel_position ]  

            elif( channel == "Xrotation" ):
                x_rotation = frameChannels[ self.channel_position ]  
                current_node.rotation = geometry.rotationMatrix_X( x_rotation ) * current_node.rotation

            elif( channel == "Yrotation" ):
                y_rotation = frameChannels[ self.channel_position ]  
                current_node.rotation = geometry.rotationMatrix_Y( y_rotation ) * current_node.rotation

            elif( channel == "Zrotation" ):
                z_rotation = frameChannels[ self.channel_position ]  
                current_node.rotation = geometry.rotationMatrix_Z( z_rotation ) * current_node.rotation

            self.channel_position += 1
        
        ### Add translation to the transformation matrix
        current_node.transformation = geometry.translationMatrix( x_position , y_position ,z_position )

        ### Add offset to the transformation matrix        
        current_node.transformation *= geometry.translationMatrix( *current_node.offset )

        ### Add rotation to the transformation matrix
        current_node.transformation *= current_node.rotation

        ### Save position to the dictionary
        self.model_position[ current_node.name ] = parent_transformation*current_node.transformation*np.matrix([[0],[0],[0],[1]])

        ### Save euler angles to the dictionary 
        self.model_eulerAngles[ current_node.name ] = ( x_rotation , y_rotation , z_rotation )

        ### Recursively call the method with the children of the current node
        for child in current_node.children:

            self.getNodePosition( parent_transformation * current_node.transformation ,
                                                                                child , 
                                                                        frameChannels )

            ### Generate the edge that joins the parent with it's child
            if(  ( self.model_position[ current_node.name ] != self.model_position[ child.name ] ).any() ):
                
                edge = np.array( [ np.array( self.model_position[ current_node.name ] ).ravel()[:3] ,
                                   np.array( self.model_position[ child.name ] ).ravel()[:3] ] )

                self.model_edges.append( edge )


