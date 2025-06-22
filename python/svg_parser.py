"""SVG Parser for converting SVG elements to polygons for nesting."""

import re
import math
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Tuple, Union
from geometry_util import Point, Polygon, degrees_to_radians

class SVGParser:
    def __init__(self):
        self.tolerance = 2.0
        self.allowed_elements = ['svg', 'circle', 'ellipse', 'path', 'polygon', 'polyline', 'rect', 'line']
    
    def set_tolerance(self, tolerance: float):
        self.tolerance = tolerance
    
    def parse_svg_string(self, svg_string: str) -> List[Polygon]:
        try:
            root = ET.fromstring(svg_string)
            return self._extract_polygons(root)
        except ET.ParseError as e:
            raise ValueError(f"Invalid SVG: {e}")
    
    def parse_svg_file(self, file_path: str) -> List[Polygon]:
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            return self._extract_polygons(root)
        except (ET.ParseError, FileNotFoundError) as e:
            raise ValueError(f"Error parsing SVG file: {e}")
    
    def _extract_polygons(self, element: ET.Element) -> List[Polygon]:
        polygons = []
        
        tag = element.tag.split('}')[-1] if '}' in element.tag else element.tag
        
        if tag in self.allowed_elements:
            polygon = self._element_to_polygon(element)
            if polygon:
                polygons.append(polygon)
        
        for child in element:
            polygons.extend(self._extract_polygons(child))
        
        return polygons
    
    def _element_to_polygon(self, element: ET.Element) -> Optional[Polygon]:
        tag = element.tag.split('}')[-1] if '}' in element.tag else element.tag
        
        if tag == 'rect':
            return self._rect_to_polygon(element)
        elif tag == 'circle':
            return self._circle_to_polygon(element)
        elif tag == 'ellipse':
            return self._ellipse_to_polygon(element)
        elif tag == 'polygon':
            return self._polygon_to_polygon(element)
        elif tag == 'polyline':
            return self._polyline_to_polygon(element)
        elif tag == 'line':
            return self._line_to_polygon(element)
        elif tag == 'path':
            return self._path_to_polygon(element)
        
        return None
    
    def _rect_to_polygon(self, element: ET.Element) -> Optional[Polygon]:
        try:
            x = float(element.get('x', 0))
            y = float(element.get('y', 0))
            width = float(element.get('width', 0))
            height = float(element.get('height', 0))
            
            if width <= 0 or height <= 0:
                return None
            
            points = [
                Point(x, y),
                Point(x + width, y),
                Point(x + width, y + height),
                Point(x, y + height)
            ]
            return Polygon(points)
        except (ValueError, TypeError):
            return None
    
    def _circle_to_polygon(self, element: ET.Element) -> Optional[Polygon]:
        try:
            cx = float(element.get('cx', 0))
            cy = float(element.get('cy', 0))
            r = float(element.get('r', 0))
            
            if r <= 0:
                return None
            
            segments = max(8, int(math.ceil(2 * math.pi / math.acos(1 - self.tolerance / r))))
            
            points = []
            for i in range(segments):
                angle = 2 * math.pi * i / segments
                x = cx + r * math.cos(angle)
                y = cy + r * math.sin(angle)
                points.append(Point(x, y))
            
            return Polygon(points)
        except (ValueError, TypeError):
            return None
    
    def _ellipse_to_polygon(self, element: ET.Element) -> Optional[Polygon]:
        try:
            cx = float(element.get('cx', 0))
            cy = float(element.get('cy', 0))
            rx = float(element.get('rx', 0))
            ry = float(element.get('ry', 0))
            
            if rx <= 0 or ry <= 0:
                return None
            
            max_r = max(rx, ry)
            segments = max(8, int(math.ceil(2 * math.pi / math.acos(1 - self.tolerance / max_r))))
            
            points = []
            for i in range(segments):
                angle = 2 * math.pi * i / segments
                x = cx + rx * math.cos(angle)
                y = cy + ry * math.sin(angle)
                points.append(Point(x, y))
            
            return Polygon(points)
        except (ValueError, TypeError):
            return None
    
    def _polygon_to_polygon(self, element: ET.Element) -> Optional[Polygon]:
        points_str = element.get('points', '')
        return self._parse_points_string(points_str)
    
    def _polyline_to_polygon(self, element: ET.Element) -> Optional[Polygon]:
        points_str = element.get('points', '')
        return self._parse_points_string(points_str)
    
    def _line_to_polygon(self, element: ET.Element) -> Optional[Polygon]:
        try:
            x1 = float(element.get('x1', 0))
            y1 = float(element.get('y1', 0))
            x2 = float(element.get('x2', 0))
            y2 = float(element.get('y2', 0))
            
            points = [Point(x1, y1), Point(x2, y2)]
            return Polygon(points)
        except (ValueError, TypeError):
            return None
    
    def _parse_points_string(self, points_str: str) -> Optional[Polygon]:
        if not points_str:
            return None
        
        points_str = re.sub(r'[,\s]+', ' ', points_str.strip())
        coords = points_str.split()
        
        if len(coords) < 4 or len(coords) % 2 != 0:
            return None
        
        points = []
        for i in range(0, len(coords), 2):
            try:
                x = float(coords[i])
                y = float(coords[i + 1])
                points.append(Point(x, y))
            except (ValueError, IndexError):
                return None
        
        return Polygon(points)
    
    def _path_to_polygon(self, element: ET.Element) -> Optional[Polygon]:
        """Convert basic path commands to polygon (simplified)."""
        d = element.get('d', '')
        if not d:
            return None
        
        points = []
        commands = re.findall(r'[MmLlHhVvZz][^MmLlHhVvZz]*', d)
        
        current_x, current_y = 0, 0
        start_x, start_y = 0, 0
        
        for command in commands:
            cmd = command[0]
            params = re.findall(r'-?\d*\.?\d+', command[1:])
            
            if cmd == 'M':
                if len(params) >= 2:
                    current_x = float(params[0])
                    current_y = float(params[1])
                    start_x, start_y = current_x, current_y
                    points.append(Point(current_x, current_y))
            
            elif cmd == 'm':
                if len(params) >= 2:
                    current_x += float(params[0])
                    current_y += float(params[1])
                    start_x, start_y = current_x, current_y
                    points.append(Point(current_x, current_y))
            
            elif cmd == 'L':
                for i in range(0, len(params), 2):
                    if i + 1 < len(params):
                        current_x = float(params[i])
                        current_y = float(params[i + 1])
                        points.append(Point(current_x, current_y))
            
            elif cmd == 'l':
                for i in range(0, len(params), 2):
                    if i + 1 < len(params):
                        current_x += float(params[i])
                        current_y += float(params[i + 1])
                        points.append(Point(current_x, current_y))
            
            elif cmd == 'H':
                for param in params:
                    current_x = float(param)
                    points.append(Point(current_x, current_y))
            
            elif cmd == 'h':
                for param in params:
                    current_x += float(param)
                    points.append(Point(current_x, current_y))
            
            elif cmd == 'V':
                for param in params:
                    current_y = float(param)
                    points.append(Point(current_x, current_y))
            
            elif cmd == 'v':
                for param in params:
                    current_y += float(param)
                    points.append(Point(current_x, current_y))
            
            elif cmd in ['Z', 'z']:
                if points and (points[-1].x != start_x or points[-1].y != start_y):
                    points.append(Point(start_x, start_y))
        
        return Polygon(points) if len(points) >= 3 else None 