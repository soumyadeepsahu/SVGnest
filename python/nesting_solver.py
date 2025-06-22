"""Nesting Solver using Genetic Algorithm for optimal placement."""

import random
import math
from typing import List, Dict, Optional, Tuple, Callable
from geometry_util import Point, Polygon, get_polygon_bounds, rotate_polygon, translate_polygon, polygon_area
from nfp_calculator import NFPCalculator

class Individual:
    def __init__(self, genes: List[Dict]):
        self.genes = genes
        self.fitness = float('inf')
        self.placements = []

class NestingSolver:
    def __init__(self):
        self.config = {
            'population_size': 10,
            'mutation_rate': 10,
            'rotations': 4,
            'spacing': 0,
            'max_generations': 50
        }
        self.nfp_calculator = NFPCalculator()
    
    def solve(self, parts: List[Polygon], container: Polygon) -> Dict:
        if not parts or not container:
            return {'fitness': float('inf'), 'placements': []}
        
        prepared_parts = []
        for i, part in enumerate(parts):
            part_data = {'id': i, 'polygon': part, 'rotations': []}
            for r in range(self.config['rotations']):
                angle = (360 / self.config['rotations']) * r
                rotated = rotate_polygon(part.points, angle)
                part_data['rotations'].append({'angle': angle, 'polygon': rotated})
            prepared_parts.append(part_data)
        
        population = []
        for _ in range(self.config['population_size']):
            genes = []
            for part in prepared_parts:
                gene = {
                    'id': part['id'],
                    'rotation': random.randint(0, len(part['rotations']) - 1)
                }
                genes.append(gene)
            random.shuffle(genes)
            population.append(Individual(genes))
        
        best_individual = None
        best_fitness = float('inf')
        no_improvement_count = 0
        
        for generation in range(self.config['max_generations']):
            generation_best = float('inf')
            
            for individual in population:
                fitness, placements = self._evaluate_fitness(individual, prepared_parts, container)
                individual.fitness = fitness
                individual.placements = placements
                
                if fitness < best_fitness:
                    best_fitness = fitness
                    best_individual = individual
                    no_improvement_count = 0
                
                generation_best = min(generation_best, fitness)
            
            # Early termination if no improvement for 10 generations
            if generation_best >= best_fitness:
                no_improvement_count += 1
                if no_improvement_count >= 10:
                    break
            
            population.sort(key=lambda x: x.fitness)
            new_population = population[:self.config['population_size']//2]
            
            while len(new_population) < self.config['population_size']:
                parent1 = random.choice(population[:5])
                parent2 = random.choice(population[:5])
                child = self._crossover(parent1, parent2)
                child = self._mutate(child)
                new_population.append(child)
            
            population = new_population
        
        return {
            'fitness': best_fitness,
            'placements': best_individual.placements if best_individual else []
        }
    
    def _evaluate_fitness(self, individual: Individual, parts: List[Dict], container: Polygon) -> Tuple[float, List[Dict]]:
        placements = []
        container_bounds = get_polygon_bounds(container.points)
        
        for gene in individual.genes:
            part = parts[gene['id']]
            rotation_data = part['rotations'][gene['rotation']]
            polygon = rotation_data['polygon']
            
            position = self._find_position(polygon, placements, container_bounds)
            if position:
                placement = {
                    'id': gene['id'],
                    'x': position['x'],
                    'y': position['y'],
                    'rotation': rotation_data['angle'],
                    'polygon': translate_polygon(polygon, position['x'], position['y'])
                }
                placements.append(placement)
        
        if not placements:
            return float('inf'), []
        
        all_points = []
        for placement in placements:
            all_points.extend(placement['polygon'])
        
        bounds = get_polygon_bounds(all_points)
        fitness = bounds['width'] * bounds['height']
        
        return fitness, placements
    
    def _find_position(self, polygon: List[Point], placed: List[Dict], container_bounds: Dict) -> Optional[Dict]:
        poly_bounds = get_polygon_bounds(polygon)
        
        # Bottom-left strategy: try bottom positions first, then left-to-right
        step_size = max(20, min(poly_bounds['width'], poly_bounds['height']) // 4)
        
        # Sort y positions from bottom to top for bottom-left strategy
        y_positions = list(range(int(container_bounds['y']), 
                                int(container_bounds['y'] + container_bounds['height'] - poly_bounds['height']), 
                                int(step_size)))
        
        for y in y_positions:
            for x in range(int(container_bounds['x']), 
                          int(container_bounds['x'] + container_bounds['width'] - poly_bounds['width']), int(step_size)):
                
                test_polygon = translate_polygon(polygon, x, y)
                test_bounds = get_polygon_bounds(test_polygon)
                
                if (test_bounds['x'] >= container_bounds['x'] and
                    test_bounds['y'] >= container_bounds['y'] and
                    test_bounds['x'] + test_bounds['width'] <= container_bounds['x'] + container_bounds['width'] and
                    test_bounds['y'] + test_bounds['height'] <= container_bounds['y'] + container_bounds['height']):
                    
                    valid = True
                    for placed_part in placed:
                        placed_bounds = get_polygon_bounds(placed_part['polygon'])
                        if self._bounds_overlap(test_bounds, placed_bounds):
                            valid = False
                            break
                    
                    if valid:
                        return {'x': x, 'y': y}
        
        return None
    
    def _bounds_overlap(self, bounds1: Dict, bounds2: Dict) -> bool:
        return not (bounds1['x'] + bounds1['width'] <= bounds2['x'] or
                   bounds2['x'] + bounds2['width'] <= bounds1['x'] or
                   bounds1['y'] + bounds1['height'] <= bounds2['y'] or
                   bounds2['y'] + bounds2['height'] <= bounds1['y'])
    
    def _crossover(self, parent1: Individual, parent2: Individual) -> Individual:
        size = len(parent1.genes)
        cut = random.randint(1, size - 1)
        
        child_genes = parent1.genes[:cut] + parent2.genes[cut:]
        return Individual(child_genes)
    
    def _mutate(self, individual: Individual) -> Individual:
        if random.randint(1, 100) <= self.config['mutation_rate']:
            if len(individual.genes) > 1:
                i, j = random.sample(range(len(individual.genes)), 2)
                individual.genes[i], individual.genes[j] = individual.genes[j], individual.genes[i]
        return individual 