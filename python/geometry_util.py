"""Core geometry utilities for SVG nesting operations."""

import math
from typing import List, Dict, Optional, Tuple, Union

TOL = 1e-9

class Point:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
    
    def __repr__(self):
        return f"Point({self.x}, {self.y})"
    
    def to_dict(self):
        return {"x": self.x, "y": self.y}

class Polygon:
    def __init__(self, points: List[Point]):
        self.points = points
        self.id = None
        self.rotation = 0
        self.children = []
    
    def __getitem__(self, index):
        return self.points[index]
    
    def __len__(self):
        return len(self.points)
    
    def __iter__(self):
        return iter(self.points)

def almost_equal(a: float, b: float, tolerance: float = TOL) -> bool:
    return abs(a - b) < tolerance

def within_distance(p1: Point, p2: Point, distance: float) -> bool:
    dx = p1.x - p2.x
    dy = p1.y - p2.y
    return (dx * dx + dy * dy) < distance * distance

def degrees_to_radians(angle: float) -> float:
    return angle * (math.pi / 180)

def radians_to_degrees(angle: float) -> float:
    return angle * (180 / math.pi)

def normalize_vector(v: Point) -> Point:
    if almost_equal(v.x * v.x + v.y * v.y, 1):
        return v
    
    length = math.sqrt(v.x * v.x + v.y * v.y)
    if length == 0:
        return Point(0, 0)
    
    inverse = 1 / length
    return Point(v.x * inverse, v.y * inverse)

def line_intersect(A: Point, B: Point, E: Point, F: Point, infinite: bool = False) -> Optional[Point]:
    """Find intersection of two line segments AB and EF."""
    a1 = B.y - A.y
    b1 = A.x - B.x
    c1 = B.x * A.y - A.x * B.y
    a2 = F.y - E.y
    b2 = E.x - F.x
    c2 = F.x * E.y - E.x * F.y
    
    denom = a1 * b2 - a2 * b1
    
    if almost_equal(denom, 0):
        return None
    
    x = (b1 * c2 - b2 * c1) / denom
    y = (a2 * c1 - a1 * c2) / denom
    
    if not (math.isfinite(x) and math.isfinite(y)):
        return None
    
    if not infinite:
        if (abs(A.x - B.x) > TOL and 
            ((A.x < B.x and (x < A.x or x > B.x)) or 
             (A.x > B.x and (x > A.x or x < B.x)))):
            return None
        
        if (abs(A.y - B.y) > TOL and 
            ((A.y < B.y and (y < A.y or y > B.y)) or 
             (A.y > B.y and (y > A.y or y < B.y)))):
            return None
        
        if (abs(E.x - F.x) > TOL and 
            ((E.x < F.x and (x < E.x or x > F.x)) or 
             (E.x > F.x and (x > E.x or x < F.x)))):
            return None
        
        if (abs(E.y - F.y) > TOL and 
            ((E.y < F.y and (y < E.y or y > F.y)) or 
             (E.y > F.y and (y > E.y or y < F.y)))):
            return None
    
    return Point(x, y)

def polygon_area(polygon: List[Point]) -> float:
    """Calculate polygon area using shoelace formula."""
    if len(polygon) < 3:
        return 0
    
    area = 0
    for i in range(len(polygon)):
        j = (i + 1) % len(polygon)
        area += polygon[i].x * polygon[j].y
        area -= polygon[j].x * polygon[i].y
    
    return area / 2

def get_polygon_bounds(polygon: List[Point]) -> Dict[str, float]:
    if not polygon:
        return {"x": 0, "y": 0, "width": 0, "height": 0}
    
    min_x = min_y = float('inf')
    max_x = max_y = float('-inf')
    
    for point in polygon:
        min_x = min(min_x, point.x)
        max_x = max(max_x, point.x)
        min_y = min(min_y, point.y)
        max_y = max(max_y, point.y)
    
    return {
        "x": min_x,
        "y": min_y,
        "width": max_x - min_x,
        "height": max_y - min_y
    }

def point_in_polygon(point: Point, polygon: List[Point]) -> bool:
    """Check if point is inside polygon using ray casting."""
    if len(polygon) < 3:
        return False
    
    x, y = point.x, point.y
    inside = False
    
    j = len(polygon) - 1
    for i in range(len(polygon)):
        xi, yi = polygon[i].x, polygon[i].y
        xj, yj = polygon[j].x, polygon[j].y
        
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    
    return inside

def rotate_polygon(polygon: List[Point], degrees: float) -> List[Point]:
    angle = degrees_to_radians(degrees)
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    
    rotated = []
    for point in polygon:
        x = point.x * cos_a - point.y * sin_a
        y = point.x * sin_a + point.y * cos_a
        rotated.append(Point(x, y))
    
    return rotated

def translate_polygon(polygon: List[Point], dx: float, dy: float) -> List[Point]:
    return [Point(p.x + dx, p.y + dy) for p in polygon]

def get_leftmost_point(polygon: List[Point]) -> Point:
    if not polygon:
        return Point(0, 0)
    
    leftmost = polygon[0]
    for point in polygon[1:]:
        if point.x < leftmost.x:
            leftmost = point
    
    return leftmost

def get_rightmost_point(polygon: List[Point]) -> Point:
    if not polygon:
        return Point(0, 0)
    
    rightmost = polygon[0]
    for point in polygon[1:]:
        if point.x > rightmost.x:
            rightmost = point
    
    return rightmost 