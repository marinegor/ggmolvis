import bpy
from abc import ABC, abstractmethod

import molecularnodes as mn
from molecularnodes.entities.trajectory import Trajectory
from molecularnodes.entities.trajectory.selections import Selection
import MDAnalysis as mda
import numpy as np
from typing import Tuple, List, Union
from pydantic import BaseModel, Field, validator, ValidationError

from .base import GGMolvisArtist
from .sceneobjects import SceneObject
from .world import World
from .camera import Camera
from .properties import Color, Material
from .utils import convert_list_to_array, look_at

class Shape(SceneObject):
    def __init__(self,
                 shape_type,
                 name=None,
                 location=None,
                 rotation=None,
                 scale=None):
        self.shape_type = shape_type
        super().__init__(
            name=name,
            location=location,
            rotation=rotation,
            scale=scale)
        

class Line(Shape):
    def __init__(self,
                 start_points: Union[List[Tuple[float, float, float]], np.ndarray],
                 end_points: Union[List[Tuple[float, float, float]], np.ndarray],
                 name=None,
                 location=None,
                 rotation=None,
                 scale=None):
        self.start_points = convert_list_to_array(start_points)
        self.end_points = convert_list_to_array(end_points)
        super().__init__(shape_type='line', name=name,
                         location=location,
                         rotation=rotation,
                         scale=scale)

    def create_object(self):
        line_data = bpy.data.curves.new(name=self.name, type='CURVE')
        line_data.dimensions = '3D'
        self.line_object = bpy.data.objects.new(self.name, line_data)
        bpy.context.scene.collection.objects.link(self.line_object)
        
        line = line_data.splines.new('POLY')
        self.line = line
        line.points.add(1)
        line.resolution_u = 4
        line.use_cyclic_u = False
        line.use_endpoint_u = True
        line.use_endpoint_v = True
        line.use_smooth = False
        
        line_data.bevel_depth = 0.004
        line_data.bevel_resolution = 10
        
        self.update_frame(bpy.context.scene.frame_current)

    def draw(self):
        pass

    def update_frame(self, frame):
        object = self.object
        start_point, end_point = self.get_points_for_frame(frame)
        object.data.splines[0].points[0].co = (start_point[0], start_point[1], start_point[2], 1.0)
        object.data.splines[0].points[1].co = (end_point[0], end_point[1], end_point[2], 1.0)
        self.world.apply_to(object, frame)

    def get_points_for_frame(self, frame: int) -> Tuple[float, float, float]:
        """Retrieve the coordinates for a specific frame"""
        points_plotted = []
        for points in [self.start_points, self.end_points]:
            if points.ndim == 2:
                if frame >= points.shape[0]:
                    frame = -1
                points_plotted.append(points[frame] * self.world_scale)
            elif points.ndim == 1:
                points_plotted.append(points * self.world_scale)
            else:
                raise ValueError("Invalid transformation coordinates")
        
        return points_plotted

    @property
    def object(self):
        return self.line_object