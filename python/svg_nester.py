"""Main SVG Nester module that provides a simple interface for nesting SVG files."""

import json
import math
from typing import List, Dict, Optional, Callable, Union, Tuple
from svg_parser import SVGParser
from geometry_util import Point, Polygon, get_polygon_bounds
from nesting_solver import NestingSolver

class SVGNester:
    def __init__(self):
        self.parser = SVGParser()
        self.solver = NestingSolver()
        self.parts = []
        self.container = None
        self.part_quantities = {}
    
    def load_svg_file(self, file_path: str) -> List[Polygon]:
        return self.parser.parse_svg_file(file_path)
    
    def load_svg_string(self, svg_string: str) -> List[Polygon]:
        return self.parser.parse_svg_string(svg_string)
    
    def create_standard_sheet(self, width: float, height: float, units: str = "mm") -> Polygon:
        sheet_points = [
            Point(0, 0),
            Point(width, 0),
            Point(width, height),
            Point(0, height)
        ]
        sheet = Polygon(sheet_points)
        sheet.width = width
        sheet.height = height
        sheet.units = units
        return sheet
    
    def estimate_max_quantity(self, part: Polygon, sheet_width: float, sheet_height: float, 
                             spacing: float = 0, rotation_angles: Optional[List[float]] = None) -> int:
        if rotation_angles is None:
            rotation_angles = [0, 90, 180, 270]
        
        from geometry_util import rotate_polygon
        
        best_estimate = 0
        
        for angle in rotation_angles:
            rotated_part = rotate_polygon(part.points, angle)
            bounds = get_polygon_bounds(rotated_part)
            
            part_width = bounds['width'] + spacing
            part_height = bounds['height'] + spacing
            
            if part_width <= sheet_width and part_height <= sheet_height:
                cols = int(sheet_width / part_width)
                rows = int(sheet_height / part_height)
                estimate = cols * rows
                best_estimate = max(best_estimate, estimate)
        
        return best_estimate
    
    def nest_max_quantity(self, part: Polygon, sheet_width: float, sheet_height: float,
                         max_attempts: int = 3, spacing: float = 0, units: str = "mm") -> Dict:
        sheet = self.create_standard_sheet(sheet_width, sheet_height, units)
        self.set_container(sheet)
        
        estimated_max = self.estimate_max_quantity(part, sheet_width, sheet_height, spacing)
        print(f"Estimated maximum quantity: {estimated_max}")
        
        best_result = None
        best_quantity = 0
        
        test_quantities = []
        
        for factor in [1.0, 0.9, 0.8, 0.7, 0.6, 0.5]:
            qty = max(1, int(estimated_max * factor))
            if qty not in test_quantities:
                test_quantities.append(qty)
        
        for qty in [1, 2, 4, 8, 16, 32]:
            if qty not in test_quantities and qty <= estimated_max:
                test_quantities.append(qty)
        
        test_quantities.sort(reverse=True)
        test_quantities = test_quantities[:max_attempts]
        
        print(f"Testing quantities: {test_quantities}")
        
        for quantity in test_quantities:
            print(f"Attempting to nest {quantity} copies...")
            
            self.set_parts([part], quantity)
            
            try:
                result = self.nest()
                placed_count = len(result['placements'])
                
                print(f"  → Successfully placed {placed_count} out of {quantity}")
                
                if placed_count > best_quantity:
                    best_quantity = placed_count
                    best_result = result.copy()
                    best_result['attempted_quantity'] = quantity
                
                if placed_count == quantity:
                    print(f"  → Perfect fit! All {quantity} parts placed.")
                    break
                    
            except Exception as e:
                print(f"  → Error with quantity {quantity}: {e}")
                continue
        
        if best_result is None:
            return {
                'success': False,
                'message': 'Could not fit any parts in the sheet',
                'sheet_dimensions': {'width': sheet_width, 'height': sheet_height, 'units': units},
                'estimated_max': estimated_max,
                'actual_quantity': 0,
                'placements': []
            }
        
        # Enhance the result with sheet-specific information
        best_result.update({
            'sheet_dimensions': {'width': sheet_width, 'height': sheet_height, 'units': units},
            'estimated_max': estimated_max,
            'actual_quantity': best_quantity,
            'efficiency': (best_quantity / estimated_max * 100) if estimated_max > 0 else 0,
            'message': f'Successfully nested {best_quantity} copies in {sheet_width}×{sheet_height} {units} sheet'
        })
        
        return best_result
    
    def create_sheet_optimization_report(self, part: Polygon, sheet_sizes: List[Dict]) -> Dict:
        results = {}
        
        for sheet_info in sheet_sizes:
            width = sheet_info['width']
            height = sheet_info['height']
            name = sheet_info.get('name', f"{width}×{height}")
            units = sheet_info.get('units', 'mm')
            
            print(f"\nTesting sheet: {name} ({width}×{height} {units})")
            
            result = self.nest_max_quantity(part, width, height, units=units)
            
            sheet_area = width * height
            parts_per_unit_area = result['actual_quantity'] / sheet_area if sheet_area > 0 else 0
            
            results[name] = {
                'sheet_info': sheet_info,
                'actual_quantity': result['actual_quantity'],
                'estimated_max': result['estimated_max'],
                'efficiency': result.get('efficiency', 0),
                'utilization': result.get('utilization', 0),
                'parts_per_unit_area': parts_per_unit_area,
                'sheet_area': sheet_area,
                'result': result
            }
        
        best_sheet = max(results.keys(), key=lambda k: results[k]['parts_per_unit_area'])
        
        return {
            'results': results,
            'best_sheet': best_sheet,
            'best_result': results[best_sheet]
        }
    
    def create_sheet_layout_svg(self, result: Dict, output_path: str, 
                               show_grid: bool = True, show_dimensions: bool = True) -> None:
        if not result.get('placements'):
            print("No placements to visualize")
            return
        
        sheet_dims = result.get('sheet_dimensions', {})
        width = sheet_dims.get('width', 100)
        height = sheet_dims.get('height', 100)
        units = sheet_dims.get('units', 'mm')
        
        margin = min(width, height) * 0.1
        svg_width = width + 2 * margin
        svg_height = height + 2 * margin
        
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{svg_width}" height="{svg_height}" 
     viewBox="{-margin} {-margin} {svg_width} {svg_height}" 
     xmlns="http://www.w3.org/2000/svg">
  
  <rect x="0" y="0" width="{width}" height="{height}" 
        fill="white" stroke="black" stroke-width="2"/>
  
'''
        
        if show_grid:
            grid_size = min(width, height) / 20
            svg_content += f'  <defs>\n'
            svg_content += f'    <pattern id="grid" width="{grid_size}" height="{grid_size}" patternUnits="userSpaceOnUse">\n'
            svg_content += f'      <path d="M {grid_size} 0 L 0 0 0 {grid_size}" fill="none" stroke="#e0e0e0" stroke-width="0.5"/>\n'
            svg_content += f'    </pattern>\n'
            svg_content += f'  </defs>\n'
            svg_content += f'  <rect x="0" y="0" width="{width}" height="{height}" fill="url(#grid)"/>\n'
        
        for i, placement in enumerate(result['placements']):
            points_str = ' '.join([f'{p.x},{p.y}' for p in placement['polygon']])
            svg_content += f'  <polygon points="{points_str}" '
            svg_content += f'fill="lightblue" fill-opacity="0.7" stroke="blue" stroke-width="1"/>\n'
        
        if show_dimensions:
            svg_content += f'  <text x="{width/2}" y="-{margin/3}" text-anchor="middle" '
            svg_content += f'font-family="Arial" font-size="{margin/4}" fill="black">'
            svg_content += f'{width} {units}</text>\n'
            
            svg_content += f'  <text x="-{margin/3}" y="{height/2}" text-anchor="middle" '
            svg_content += f'font-family="Arial" font-size="{margin/4}" fill="black" '
            svg_content += f'transform="rotate(-90, -{margin/3}, {height/2})">'
            svg_content += f'{height} {units}</text>\n'
        
        stats_y = height + margin * 0.3
        font_size = margin / 5
        
        svg_content += f'''  
  <text x="0" y="{stats_y}" font-family="Arial" font-size="{font_size}" fill="black">
    Parts: {result.get('actual_quantity', 0)} | Utilization: {result.get('utilization', 0):.1f}% | Efficiency: {result.get('efficiency', 0):.1f}%
  </text>
  <text x="0" y="{stats_y + font_size * 1.5}" font-family="Arial" font-size="{font_size * 0.8}" fill="gray">
    Sheet: {width}×{height} {units} | Estimated max: {result.get('estimated_max', 0)}
  </text>
'''
        
        svg_content += '</svg>'
        
        with open(output_path, 'w') as f:
            f.write(svg_content)
        
        print(f"Sheet layout saved to {output_path}")
    
    def set_parts(self, parts: List[Polygon], quantities: Optional[Union[int, List[int]]] = None):
        if quantities is None:
            quantities = [1] * len(parts)
        elif isinstance(quantities, int):
            quantities = [quantities] * len(parts)
        
        if len(quantities) != len(parts):
            raise ValueError("Number of quantities must match number of parts")
        
        self.original_parts = parts.copy()
        self.part_quantities = {}
        
        self.parts = []
        for i, (part, quantity) in enumerate(zip(parts, quantities)):
            self.part_quantities[i] = quantity
            for copy_num in range(quantity):
                new_part = Polygon(part.points.copy())
                new_part.id = len(self.parts)
                new_part.original_id = i
                new_part.copy_number = copy_num
                self.parts.append(new_part)
    
    def set_parts_with_quantities(self, parts_with_quantities: List[Dict]):
        parts = []
        quantities = []
        
        for item in parts_with_quantities:
            if not isinstance(item, dict) or 'part' not in item or 'quantity' not in item:
                raise ValueError("Each item must be a dict with 'part' and 'quantity' keys")
            
            parts.append(item['part'])
            quantities.append(item['quantity'])
        
        self.set_parts(parts, quantities)
    
    def duplicate_part(self, part_index: int, additional_copies: int):
        if part_index >= len(self.original_parts):
            raise ValueError(f"Part index {part_index} out of range")
        
        original_part = self.original_parts[part_index]
        current_quantity = self.part_quantities.get(part_index, 0)
        
        for copy_num in range(current_quantity, current_quantity + additional_copies):
            new_part = Polygon(original_part.points.copy())
            new_part.id = len(self.parts)
            new_part.original_id = part_index
            new_part.copy_number = copy_num
            self.parts.append(new_part)
        
        self.part_quantities[part_index] = current_quantity + additional_copies
    
    def get_part_quantities(self) -> Dict[int, int]:
        return self.part_quantities.copy()
    
    def get_total_parts_count(self) -> int:
        return len(self.parts)
    
    def set_container(self, container: Polygon):
        self.container = container
        self.container.id = -1
    
    def configure(self, config: Dict):
        if 'curve_tolerance' in config:
            self.parser.set_tolerance(config['curve_tolerance'])
        
        self.solver.config.update(config)
    
    def nest(self, progress_callback: Optional[Callable] = None) -> Dict:
        if not self.parts or not self.container:
            raise ValueError("Parts and container must be set before nesting")
        
        result = self.solver.solve(self.parts, self.container)
        
        result.update({
            'success': True,
            'utilization': self._calculate_utilization(result['placements']),
            'total_original_parts': len(self.original_parts) if hasattr(self, 'original_parts') else len(set(p.original_id for p in self.parts if hasattr(p, 'original_id'))),
            'total_part_instances': len(self.parts),
            'placed_instances': len(result['placements']),
            'part_quantities': self.part_quantities.copy(),
            'message': f"Placed {len(result['placements'])} out of {len(self.parts)} part instances"
        })
        
        return result
    
    def _calculate_utilization(self, placements: List[Dict]) -> float:
        if not placements or not self.container:
            return 0
        
        from geometry_util import polygon_area
        
        container_area = abs(polygon_area(self.container.points))
        if container_area == 0:
            return 0
        
        total_part_area = 0
        for placement in placements:
            total_part_area += abs(polygon_area(placement['polygon']))
        
        return (total_part_area / container_area) * 100
    
    def export_result(self, result: Dict, output_path: str):
        export_data = {
            'success': result['success'],
            'fitness': result['fitness'],
            'utilization': result['utilization'],
            'message': result['message'],
            'total_original_parts': result.get('total_original_parts', 0),
            'total_part_instances': result.get('total_part_instances', 0),
            'placed_instances': result.get('placed_instances', 0),
            'part_quantities': result.get('part_quantities', {}),
            'sheet_dimensions': result.get('sheet_dimensions', {}),
            'actual_quantity': result.get('actual_quantity', 0),
            'estimated_max': result.get('estimated_max', 0),
            'efficiency': result.get('efficiency', 0),
            'placements': []
        }
        
        for placement in result['placements']:
            placement_data = {
                'id': placement['id'],
                'original_id': getattr(self.parts[placement['id']], 'original_id', placement['id']) if placement['id'] < len(self.parts) else placement['id'],
                'copy_number': getattr(self.parts[placement['id']], 'copy_number', 0) if placement['id'] < len(self.parts) else 0,
                'x': placement['x'],
                'y': placement['y'],
                'rotation': placement['rotation'],
                'points': [{'x': p.x, 'y': p.y} for p in placement['polygon']]
            }
            export_data['placements'].append(placement_data)
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
    
    def create_result_svg(self, result: Dict, output_path: str, show_part_labels: bool = True):
        if not result['placements']:
            return
        
        from geometry_util import get_polygon_bounds
        
        all_points = []
        for placement in result['placements']:
            all_points.extend(placement['polygon'])
        
        bounds = get_polygon_bounds(all_points)
        
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{bounds['width'] + 20}" height="{bounds['height'] + 20}" 
     viewBox="{bounds['x'] - 10} {bounds['y'] - 10} {bounds['width'] + 20} {bounds['height'] + 20}" 
     xmlns="http://www.w3.org/2000/svg">
  
  <polygon points="{' '.join([f'{p.x},{p.y}' for p in self.container.points])}" 
           fill="none" stroke="black" stroke-width="2"/>
  
'''
        
        colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'cyan', 'magenta']
        
        for i, placement in enumerate(result['placements']):
            part_id = placement['id']
            original_id = getattr(self.parts[part_id], 'original_id', part_id) if part_id < len(self.parts) else 0
            copy_number = getattr(self.parts[part_id], 'copy_number', 0) if part_id < len(self.parts) else 0
            
            color = colors[original_id % len(colors)]
            points_str = ' '.join([f'{p.x},{p.y}' for p in placement['polygon']])
            
            svg_content += f'''  <polygon points="{points_str}" 
           fill="{color}" fill-opacity="0.5" stroke="{color}" stroke-width="1"/>
'''
            
            if show_part_labels:
                center_x = sum(p.x for p in placement['polygon']) / len(placement['polygon'])
                center_y = sum(p.y for p in placement['polygon']) / len(placement['polygon'])
                
                label = f"{original_id}.{copy_number + 1}"
                svg_content += f'''  <text x="{center_x}" y="{center_y}" 
           text-anchor="middle" dominant-baseline="middle" 
           font-family="Arial" font-size="8" fill="black">{label}</text>
'''
        
        svg_content += '</svg>'
        
        with open(output_path, 'w') as f:
            f.write(svg_content)
    
    def print_nesting_summary(self, result: Dict):
        print("=== Nesting Summary ===")
        
        if 'sheet_dimensions' in result:
            dims = result['sheet_dimensions']
            print(f"Sheet size: {dims.get('width', 'N/A')} × {dims.get('height', 'N/A')} {dims.get('units', '')}")
        
        print(f"Original part types: {result.get('total_original_parts', 'N/A')}")
        print(f"Total part instances: {result.get('total_part_instances', 'N/A')}")
        print(f"Successfully placed: {result.get('placed_instances', 'N/A')}")
        
        if 'actual_quantity' in result:
            print(f"Actual quantity achieved: {result['actual_quantity']}")
        if 'estimated_max' in result:
            print(f"Estimated maximum: {result['estimated_max']}")
        if 'efficiency' in result:
            print(f"Nesting efficiency: {result['efficiency']:.1f}%")
        
        print(f"Material utilization: {result.get('utilization', 0):.1f}%")
        print(f"Fitness score: {result.get('fitness', 'N/A')}")
        
        if 'part_quantities' in result:
            print("\nPart quantities:")
            for original_id, quantity in result['part_quantities'].items():
                placed_count = sum(1 for p in result['placements'] 
                                 if getattr(self.parts[p['id']], 'original_id', p['id']) == original_id)
                print(f"  Part {original_id}: {placed_count}/{quantity} placed")
        
        print(f"\nMessage: {result.get('message', 'N/A')}")


def main():
    nester = SVGNester()
    
    nester.configure({
        'population_size': 10,     # Reduced from 20
        'max_generations': 25,     # Reduced from 50
        'rotations': 2,            # Reduced from 4 (0°, 180°)
        'mutation_rate': 15,
        'spacing': 5
    })
    
    try:
        parts = nester.load_svg_file('python/blank_outline.svg')
        part = parts[0]
        print("Loaded part from blank_outline.svg")
        
        result = nester.nest_max_quantity(
            part=part,
            sheet_width=2500,
            sheet_height=1250,
            max_attempts=3,  # Reduced from 5
            spacing=5,
            units="mm"
        )
        
        if result.get('success', False):
            print(f"Successfully nested {result['actual_quantity']} parts")
            print(f"Utilization: {result.get('utilization', 0):.1f}%")
            
            nester.create_sheet_layout_svg(result, 'sheet_layout.svg')
            nester.export_result(result, 'result.json')
            
        else:
            print(f"Nesting failed: {result.get('message', 'Unknown error')}")
            
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main() 