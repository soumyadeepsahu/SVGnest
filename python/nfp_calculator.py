"""No-Fit Polygon (NFP) Calculator for SVG nesting."""

import math
from typing import List, Dict, Optional, Tuple
from geometry_util import Point, Polygon, almost_equal, line_intersect, polygon_area, point_in_polygon

class NFPCalculator:
    def __init__(self):
        self.tolerance = 1e-6
    
    def calculate_nfp(self, stationary: List[Point], moving: List[Point]) -> List[List[Point]]:
        """Calculate NFP for moving polygon relative to stationary polygon."""
        if len(stationary) < 3 or len(moving) < 3:
            return []
        
        if polygon_area(stationary) < 0:
            stationary = list(reversed(stationary))
        if polygon_area(moving) > 0:
            moving = list(reversed(moving))
        
        nfp_points = []
        
        for i in range(len(stationary)):
            edge_start = stationary[i]
            edge_end = stationary[(i + 1) % len(stationary)]
            
            nfp_segment = self._calculate_nfp_segment(edge_start, edge_end, moving)
            nfp_points.extend(nfp_segment)
        
        if len(nfp_points) < 3:
            return []
        
        nfp_points = self._remove_duplicate_points(nfp_points)
        
        return [nfp_points] if len(nfp_points) >= 3 else []
    
    def _calculate_nfp_segment(self, edge_start: Point, edge_end: Point, moving: List[Point]) -> List[Point]:
        reference_point = moving[0]
        
        segment = []
        
        nfp_start = Point(edge_start.x - reference_point.x, edge_start.y - reference_point.y)
        nfp_end = Point(edge_end.x - reference_point.x, edge_end.y - reference_point.y)
        
        segment.append(nfp_start)
        segment.append(nfp_end)
        
        return segment
    
    def _remove_duplicate_points(self, points: List[Point]) -> List[Point]:
        if not points:
            return []
        
        cleaned = [points[0]]
        for i in range(1, len(points)):
            if not (almost_equal(points[i].x, cleaned[-1].x) and 
                   almost_equal(points[i].y, cleaned[-1].y)):
                cleaned.append(points[i])
        
        if (len(cleaned) > 1 and 
            almost_equal(cleaned[-1].x, cleaned[0].x) and 
            almost_equal(cleaned[-1].y, cleaned[0].y)):
            cleaned.pop()
        
        return cleaned
    
    def calculate_inner_nfp(self, container: List[Point], part: List[Point]) -> List[List[Point]]:
        """Calculate inner NFP - area where part can be placed inside container."""
        if len(container) < 3 or len(part) < 3:
            return []
        
        min_x = min(p.x for p in part)
        max_x = max(p.x for p in part)
        min_y = min(p.y for p in part)
        max_y = max(p.y for p in part)
        
        width = max_x - min_x
        height = max_y - min_y
        
        offset_x = width / 2
        offset_y = height / 2
        
        inner_nfp = []
        for point in container:
            inner_nfp.append(Point(point.x - offset_x, point.y - offset_y))
        
        return [inner_nfp] if len(inner_nfp) >= 3 else []
    
    def point_in_nfp(self, point: Point, nfp: List[Point]) -> bool:
        return point_in_polygon(point, nfp)
    
    def nfp_intersect(self, nfp1: List[Point], nfp2: List[Point]) -> List[List[Point]]:
        """Calculate intersection of two NFPs (simplified)."""
        area1 = abs(polygon_area(nfp1))
        area2 = abs(polygon_area(nfp2))
        
        if area1 < area2:
            return [nfp1] if area1 > 0 else []
        else:
            return [nfp2] if area2 > 0 else []
    
    def simplify_nfp(self, nfp: List[Point], tolerance: float = None) -> List[Point]:
        if tolerance is None:
            tolerance = self.tolerance
        
        if len(nfp) < 3:
            return nfp
        
        simplified = []
        
        for i in range(len(nfp)):
            current = nfp[i]
            prev_point = nfp[i - 1]
            next_point = nfp[(i + 1) % len(nfp)]
            
            if not self._point_on_line(prev_point, next_point, current, tolerance):
                simplified.append(current)
        
        return simplified if len(simplified) >= 3 else nfp
    
    def _point_on_line(self, p1: Point, p2: Point, point: Point, tolerance: float) -> bool:
        dx = p2.x - p1.x
        dy = p2.y - p1.y
        
        if almost_equal(dx, 0) and almost_equal(dy, 0):
            return False
        
        distance = abs(dy * point.x - dx * point.y + p2.x * p1.y - p2.y * p1.x) / math.sqrt(dx * dx + dy * dy)
        
        return distance < tolerance 