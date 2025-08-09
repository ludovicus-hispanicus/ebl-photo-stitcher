'''
Results of previous runs:
- Brute force (grid search): 13.8 hours, 92,400 combinations, 0 successful
- Flexible search: Best coverage: 57.1%, Parameters: {'hough_threshold': 130, 'hough_min_line_length': 46, 'tick_min_height': 68, 'canny_low_threshold': 17, 'canny_high_threshold': 89, 'roi_height_fraction': 0.51}
'''

import os
import sys
import itertools
import time
import argparse
import cv2
import random
import numpy as np

# Add required directories to path
script_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
lib_directory = os.path.join(script_directory, "lib")
tests_directory = os.path.dirname(os.path.abspath(__file__))

for directory in [lib_directory, tests_directory]:
    if directory not in sys.path:
        sys.path.insert(0, directory)

from ruler_detector_iraq_museum import detect_1cm_distance_iraq, get_detection_parameters
from test_config import EXPECTED_MEASUREMENTS


class RulerParameterOptimizer:
    """Clean, streamlined ruler detection parameter optimization."""
    
    def __init__(self, test_images_path):
        self.test_images_path = test_images_path
        self.expected_measurements = EXPECTED_MEASUREMENTS
        
    def diagnose(self):
        """Quick diagnostic of current detection performance."""
        print("=== DIAGNOSTIC ===")
        for image_name, expected_data in self.expected_measurements.items():
            image_path = os.path.join(self.test_images_path, image_name)
            if not os.path.exists(image_path):
                continue
                
            try:
                detected = detect_1cm_distance_iraq(image_path, museum_selection="Iraq Museum (Sippar Library)")
                expected = expected_data['expected']
                min_val, max_val = expected_data['min'], expected_data['max']
                
                if detected is None:
                    status = "❌ NO DETECTION"
                elif min_val <= detected <= max_val:
                    status = f"✅ PASS ({abs(detected - expected):.0f}px error)"
                else:
                    status = f"❌ FAIL ({abs(detected - expected):.0f}px error)"
                
                print(f"{image_name}: {detected}px (expected {expected}px) - {status}")
                
            except Exception as e:
                print(f"{image_name}: ❌ ERROR - {e}")
    
    def test_parameters(self, params, distance_filter=None):
        """Test parameter set on all images."""
        results = {}
        total_error = 0
        successful = 0
        
        for image_name, expected_data in self.expected_measurements.items():
            image_path = os.path.join(self.test_images_path, image_name)
            if not os.path.exists(image_path):
                continue
            
            if distance_filter:
                detected = self._detect_with_distance_filter(image_path, params, *distance_filter)
            else:
                detected = self._detect_with_params(image_path, params)
            
            results[image_name] = detected
            
            if detected and expected_data['min'] <= detected <= expected_data['max']:
                successful += 1
                total_error += abs(detected - expected_data['expected'])
        
        coverage = successful / len(self.expected_measurements)
        return results, successful, coverage, total_error
    
    def _detect_with_params(self, image_path, params):
        """Run detection with custom parameters."""
        try:
            # This would require modifying the original function to accept parameters
            # For now, use distance filtering approach
            return self._detect_with_distance_filter(image_path, params, 400, 1000)
        except:
            return None
    
    def _detect_with_distance_filter(self, image_path, params, min_distance, max_distance):
        """Detect with custom parameters and distance filtering."""
        try:
            image = cv2.imread(image_path)
            if image is None:
                return None
            
            height, width = image.shape[:2]
            roi_height = int(height * params['roi_height_fraction'])
            roi = image[height - roi_height:, :]
            
            # Process image
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blurred, params['canny_low_threshold'], params['canny_high_threshold'])
            
            # Detect lines
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, 
                                   threshold=params['hough_threshold'],
                                   minLineLength=params['hough_min_line_length'], 
                                   maxLineGap=10)
            
            if lines is None:
                return None
            
            # Filter vertical lines
            vertical_lines = []
            for line in lines:
                x1, y1, x2, y2 = line[0]
                if x2 - x1 != 0:
                    angle = abs(np.arctan((y2 - y1) / (x2 - x1)) * 180 / np.pi)
                else:
                    angle = 90
                
                if 80 <= angle <= 90:
                    line_length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                    if line_length >= params['tick_min_height']:
                        vertical_lines.append(x1)
            
            if len(vertical_lines) < 2:
                return None
            
            # Calculate distances
            vertical_lines.sort()
            distances = []
            for i in range(len(vertical_lines) - 1):
                dist = abs(vertical_lines[i + 1] - vertical_lines[i])
                if min_distance <= dist <= max_distance:
                    distances.append(dist)
            
            if not distances:
                return None
            
            # Return most common distance
            return float(max(set(distances), key=distances.count))
            
        except:
            return None
    
    def flexible_search(self, target_coverage=0.7, max_iterations=1000):
        print(f"=== FLEXIBLE SEARCH ===")
        print(f"Target: {target_coverage*100:.0f}% success rate")
        param_ranges = {
            'hough_threshold': (40, 150),
            'hough_min_line_length': (10, 100),
            'hough_max_line_gap': (5, 40),
            'tick_max_width': (10, 40),
            'tick_min_width': (1, 10),
            'tick_min_height': (10, 60),
            'max_tick_thickness_px': (10, 40),
            'min_ticks_required': (7, 15),
            'num_ticks_for_1cm': (7, 15),
            'consistency_threshold': (0.5, 1.0),
            'canny_low_threshold': (1, 30),
            'canny_high_threshold': (20, 100),
            'roi_height_fraction': (0.2, 0.8),
        }
        
        best_coverage = 0
        best_params = None
        best_results = None
        
        start_time = time.time()
        
        for i in range(max_iterations):
            # Generate random parameters
            params = {}
            for param, (low, high) in param_ranges.items():
                if param == 'roi_height_fraction':
                    params[param] = round(random.uniform(low, high), 2)
                else:
                    params[param] = random.randint(int(low), int(high))
            
            # Test with multiple distance filters
            best_coverage_for_params = 0
            best_results_for_params = None
            
            for min_dist, max_dist in [(400, 1000), (500, 900), (300, 800)]:
                results, successful, coverage, error = self.test_parameters(
                    params, distance_filter=(min_dist, max_dist)
                )
                
                if coverage > best_coverage_for_params:
                    best_coverage_for_params = coverage
                    best_results_for_params = results
            
            # Update best if this is better
            if best_coverage_for_params > best_coverage:
                best_coverage = best_coverage_for_params
                best_params = params
                best_results = best_results_for_params
                
                print(f"*** NEW BEST! Iteration {i}: {best_coverage*100:.1f}% success")
                print(f"    Params: {params}")
                
                if best_coverage >= target_coverage:
                    print(f"✅ Target achieved!")
                    break
            
            if i % 200 == 0:
                elapsed = time.time() - start_time
                print(f"Progress: {i}/{max_iterations} - Best: {best_coverage*100:.1f}% ({elapsed:.0f}s)")
        
        elapsed_time = time.time() - start_time
        successful_images = int(best_coverage * len(self.expected_measurements))
        
        print(f"\nFlexible search complete: {elapsed_time/60:.1f}min")
        print(f"Best coverage: {successful_images}/{len(self.expected_measurements)} ({best_coverage*100:.1f}%)")
        
        return best_params, best_results, best_coverage
    
    def grid_search(self, flexible=True, target_coverage=0.7):
        """Systematic grid search with optional flexible criteria."""
        print("=== GRID SEARCH ===")
        print(f"Mode: {'Flexible' if flexible else 'Strict'}")
        
        param_grid = {
            'hough_threshold': [60, 80, 100, 120],
            'hough_min_line_length': [20, 40, 60, 80],
            'tick_min_height': [25, 40, 60, 80],
            'canny_low_threshold': [15, 20, 25],
            'canny_high_threshold': [45, 60, 75],
            'roi_height_fraction': [0.3, 0.4, 0.5, 0.6],
        }
        
        combinations = list(itertools.product(*param_grid.values()))
        total = len(combinations)
        print(f"Testing {total:,} combinations")
        
        best_coverage = 0
        best_params = None
        best_results = None
        best_error = float('inf')
        
        start_time = time.time()
        
        for i, combination in enumerate(combinations):
            params = dict(zip(param_grid.keys(), combination))
            
            if i % 200 == 0:
                elapsed = time.time() - start_time
                print(f"Progress: {i:,}/{total:,} ({i/total*100:.1f}%) - Best: {best_coverage*100:.1f}%")
            
            # Test with multiple distance filters if flexible
            if flexible:
                best_coverage_for_params = 0
                best_results_for_params = None
                best_error_for_params = float('inf')
                
                for min_dist, max_dist in [(400, 1000), (500, 900), (300, 800)]:
                    results, successful, coverage, error = self.test_parameters(
                        params, distance_filter=(min_dist, max_dist)
                    )
                    
                    if coverage > best_coverage_for_params or (coverage == best_coverage_for_params and error < best_error_for_params):
                        best_coverage_for_params = coverage
                        best_results_for_params = results
                        best_error_for_params = error
                
                coverage = best_coverage_for_params
                results = best_results_for_params
                error = best_error_for_params
            else:
                # Strict mode - must work for all images
                results, successful, coverage, error = self.test_parameters(params)
                if coverage < 1.0:  # Not all images passed
                    continue
            
            # Check if this is better
            target_met = coverage >= target_coverage if flexible else coverage == 1.0
            
            if target_met and (coverage > best_coverage or (coverage == best_coverage and error < best_error)):
                best_coverage = coverage
                best_params = params
                best_results = results
                best_error = error
                
                print(f"*** NEW BEST! Coverage: {coverage*100:.1f}% - Error: {error:.1f}px")
                print(f"    Params: {params}")
        
        elapsed_time = time.time() - start_time
        successful_images = int(best_coverage * len(self.expected_measurements))
        
        print(f"\nGrid search complete: {elapsed_time/60:.1f}min")
        print(f"Best coverage: {successful_images}/{len(self.expected_measurements)} ({best_coverage*100:.1f}%)")
        
        return best_params, best_results, best_coverage
    
    def quick_test(self):
        """Quick test with a few predefined parameter sets."""
        print("=== QUICK TEST ===")
        
        param_sets = [
            {'name': 'Conservative', 'hough_threshold': 100, 'hough_min_line_length': 50, 'tick_min_height': 60,
             'canny_low_threshold': 25, 'canny_high_threshold': 75, 'roi_height_fraction': 0.4},
            {'name': 'Moderate', 'hough_threshold': 80, 'hough_min_line_length': 30, 'tick_min_height': 40,
             'canny_low_threshold': 20, 'canny_high_threshold': 60, 'roi_height_fraction': 0.5},
            {'name': 'Sensitive', 'hough_threshold': 60, 'hough_min_line_length': 20, 'tick_min_height': 25,
             'canny_low_threshold': 15, 'canny_high_threshold': 45, 'roi_height_fraction': 0.6}
        ]
        
        best_coverage = 0
        best_params = None
        
        for param_set in param_sets:
            name = param_set.pop('name')
            print(f"\n--- {name} ---")
            
            for min_dist, max_dist in [(400, 1000), (500, 900), (300, 800)]:
                results, successful, coverage, error = self.test_parameters(
                    param_set, distance_filter=(min_dist, max_dist)
                )
                
                print(f"  Distance filter {min_dist}-{max_dist}px: {coverage*100:.1f}% success")
                
                if coverage > best_coverage:
                    best_coverage = coverage
                    best_params = param_set.copy()
                    best_params['distance_filter'] = (min_dist, max_dist)
        
        successful_images = int(best_coverage * len(self.expected_measurements))
        print(f"\nQuick test best: {successful_images}/{len(self.expected_measurements)} ({best_coverage*100:.1f}%)")
        
        return best_params, best_coverage
    
    def print_results(self, results, params):
        """Print detailed results."""
        if not results:
            print("No results to display")
            return
        
        print(f"\nParameters: {params}")
        print("\nDetailed Results:")
        
        for image_name, detected in results.items():
            expected = self.expected_measurements[image_name]['expected']
            min_val, max_val = self.expected_measurements[image_name]['min'], self.expected_measurements[image_name]['max']
            
            if detected and min_val <= detected <= max_val:
                error = abs(detected - expected)
                print(f"✅ {image_name}: {detected}px (expected {expected}px, error {error:.1f}px)")
            else:
                print(f"❌ {image_name}: {detected}px (expected {expected}px)")


def main():
    """Main function with clean command line interface."""
    parser = argparse.ArgumentParser(description="Ruler detection parameter optimization")
    parser.add_argument("--diagnose", action="store_true", help="Quick diagnostic")
    parser.add_argument("--quick", action="store_true", help="Quick test with predefined parameters")
    parser.add_argument("--flexible", action="store_true", help="Flexible random search (RECOMMENDED)")
    parser.add_argument("--grid", action="store_true", help="Systematic grid search")
    parser.add_argument("--strict", action="store_true", help="Strict grid search (100% success required)")
    parser.add_argument("--target-coverage", type=float, default=0.7, help="Target success rate (default: 0.7)")
    parser.add_argument("--iterations", type=int, default=1000, help="Max iterations for flexible search")
    
    args = parser.parse_args()
    
    # Setup
    test_images_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Examples", "Sippar")
    
    if not os.path.exists(test_images_path):
        print(f"ERROR: Test images directory not found: {test_images_path}")
        return
    
    print(f"Test images directory: {test_images_path}")
    optimizer = RulerParameterOptimizer(test_images_path)
    
    # Run selected operation
    if args.diagnose:
        optimizer.diagnose()
    
    elif args.quick:
        best_params, coverage = optimizer.quick_test()
        print(f"\nBest quick test result: {coverage*100:.1f}% success")
        print(f"Parameters: {best_params}")
    
    elif args.flexible:
        best_params, results, coverage = optimizer.flexible_search(
            target_coverage=args.target_coverage, 
            max_iterations=args.iterations
        )
        if best_params:
            optimizer.print_results(results, best_params)
        else:
            print("No successful parameters found")
    
    elif args.grid:
        best_params, results, coverage = optimizer.grid_search(
            flexible=True, 
            target_coverage=args.target_coverage
        )
        if best_params:
            optimizer.print_results(results, best_params)
        else:
            print("No successful parameters found")
    
    elif args.strict:
        best_params, results, coverage = optimizer.grid_search(
            flexible=False
        )
        if best_params:
            optimizer.print_results(results, best_params)
        else:
            print("No parameters work for 100% of images")
    
    else:
        print("No operation selected. Use --help for options.")
        print("\nRECOMMENDED:")
        print("  --diagnose    # See current performance (30 sec)")
        print("  --quick       # Test predefined parameters (1 min)")  
        print("  --flexible    # Smart search for majority success (5-15 min)")


if __name__ == "__main__":
    main()