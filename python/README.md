# SVG Nesting Library

Python library for nesting SVG shapes using genetic algorithms to minimize material waste.

## Features

- Parse SVG files and convert shapes to polygons
- Genetic algorithm-based optimization with rotation support
- Standard sheet nesting for manufacturing
- Configurable parameters and multiple output formats

## Quick Start

### Standard Sheet Nesting (Manufacturing)
```python
from svg_nester import SVGNester
from geometry_util import Point, Polygon

# Create nester instance
nester = SVGNester()

# Create a part (100×50mm rectangle)
part = Polygon([Point(0, 0), Point(100, 0), Point(100, 50), Point(0, 50)])

# Nest maximum quantity in standard 2.5×1.25m sheet
result = nester.nest_max_quantity(
    part=part,
    sheet_width=2500,
    sheet_height=1250,
    spacing=3,
    units="mm"
)

print(f"Nested {result['actual_quantity']} parts!")
print(f"Utilization: {result['utilization']:.1f}%")

# Create sheet layout visualization
nester.create_sheet_layout_svg(result, 'sheet_layout.svg')
```

### Custom Container Nesting
```python
from svg_nester import SVGNester
from geometry_util import Point, Polygon

# Create nester instance
nester = SVGNester()

# Configure parameters
nester.configure({
    'population_size': 20,
    'max_generations': 100,
    'rotations': 4,
    'mutation_rate': 15,
    'spacing': 2
})

# Load parts from SVG file
parts = nester.load_svg_file('parts.svg')
nester.set_parts(parts)

# Define container
container_points = [
    Point(0, 0),
    Point(200, 0),
    Point(200, 100),
    Point(0, 100)
]
nester.set_container(Polygon(container_points))

# Perform nesting
result = nester.nest()

# Export results
nester.export_result(result, 'result.json')
nester.create_result_svg(result, 'result.svg')
```

## Modules

- `geometry_util.py` - Core geometry operations (Point, Polygon, transformations)
- `svg_parser.py` - SVG parsing and shape conversion  
- `nfp_calculator.py` - No-Fit Polygon calculations
- `nesting_solver.py` - Genetic algorithm solver
- `svg_nester.py` - Main API with sheet nesting support

## Configuration

- `population_size`: GA population size (default: 10)
- `max_generations`: Maximum generations (default: 50)
- `rotations`: Rotation angles to try (default: 4)
- `mutation_rate`: Mutation rate % (default: 10)
- `spacing`: Min spacing between parts (default: 0)

## Additional Examples

Multiple copies:
```python
nester.set_parts(parts, [5, 3, 2])  # Different quantities
```

Sheet optimization:
```python
sheet_sizes = [
    {'width': 2500, 'height': 1250, 'name': 'Standard'},
    {'width': 3000, 'height': 1500, 'name': 'Large'}
]
optimization = nester.create_sheet_optimization_report(part, sheet_sizes)
```

## Limitations

This is a simplified implementation focused on essential nesting functionality:

- Basic NFP calculations (simplified)
- Limited SVG path support (no curves, arcs)
- Simplified polygon clipping
- Basic genetic algorithm implementation

For production use, consider integrating with libraries like:
- `shapely` for robust polygon operations
- `svgpathtools` for comprehensive SVG path parsing
- `clipper` for advanced polygon clipping

## License

Based on the original SVGnest JavaScript library (MIT License). 