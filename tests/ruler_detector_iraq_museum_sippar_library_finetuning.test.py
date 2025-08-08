import os
import sys
import pytest
import itertools
import numpy as np
import time
import multiprocessing as mp
from multiprocessing import Pool, Manager
import math
import argparse

# Add the lib directory to the path to import the module
script_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
lib_directory = os.path.join(script_directory, "lib")
if lib_directory not in sys.path:
    sys.path.insert(0, lib_directory)

# Add tests directory to path for test_config
tests_directory = os.path.dirname(os.path.abspath(__file__))
if tests_directory not in sys.path:
    sys.path.insert(0, tests_directory)

from ruler_detector_iraq_museum import detect_1cm_distance_iraq, get_detection_parameters
from test_config import EXPECTED_MEASUREMENTS


def test_parameter_combination(args):
    """
    Test a single parameter combination.
    This function will be run in parallel by multiple processes when using --parallel.
    """
    combination_index, combination, test_images_path = args
    
    # Re-import modules in each process (necessary for multiprocessing)
    import sys
    import os
    
    # Re-add paths for each process
    script_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    lib_directory = os.path.join(script_directory, "lib")
    if lib_directory not in sys.path:
        sys.path.insert(0, lib_directory)
    
    tests_directory = os.path.dirname(os.path.abspath(__file__))
    if tests_directory not in sys.path:
        sys.path.insert(0, tests_directory)
    
    from ruler_detector_iraq_museum import detect_1cm_distance_iraq, get_detection_parameters
    from test_config import EXPECTED_MEASUREMENTS
    
    param_names = ['hough_threshold', 'hough_min_line_length', 'tick_min_height', 
                   'canny_low_threshold', 'canny_high_threshold', 'roi_height_fraction']
    current_params = dict(zip(param_names, combination))
    
    try:
        # Mock the get_detection_parameters function for this process
        original_get_params = get_detection_parameters
        
        def mock_get_detection_parameters(museum_selection="Iraq Museum"):
            if museum_selection == "Iraq Museum (Sippar Library)":
                new_params = original_get_params("Iraq Museum (Sippar Library)").copy()
                # Update all parameters including roi_height_fraction
                new_params.update(current_params)
                return new_params
            return original_get_params(museum_selection)
        
        # Temporarily replace the function
        sys.modules['ruler_detector_iraq_museum'].get_detection_parameters = mock_get_detection_parameters
        
        total_error = 0
        all_images_passed = True
        current_results = {}
        failed_images = []
        
        for image_name, expected_data in EXPECTED_MEASUREMENTS.items():
            image_path = os.path.join(test_images_path, image_name)
            
            if not os.path.exists(image_path):
                continue
            
            try:
                # Now properly pass the roi_height_fraction parameter
                detected_distance = detect_1cm_distance_iraq(
                    image_path, 
                    museum_selection="Iraq Museum (Sippar Library)",
                    roi_height_fraction=current_params['roi_height_fraction']
                )
                current_results[image_name] = detected_distance
                
                if detected_distance is None:
                    all_images_passed = False
                    failed_images.append(f"{image_name} (no detection)")
                    total_error = float('inf')
                    break
                elif not (expected_data['min'] <= detected_distance <= expected_data['max']):
                    all_images_passed = False
                    failed_images.append(f"{image_name} ({detected_distance}px outside range {expected_data['min']}-{expected_data['max']})")
                    total_error = float('inf')
                    break
                
                total_error += abs(detected_distance - expected_data['expected'])
                
            except Exception as e:
                all_images_passed = False
                failed_images.append(f"{image_name} (error: {str(e)[:30]})")
                total_error = float('inf')
                break
        
        # Restore the original function
        sys.modules['ruler_detector_iraq_museum'].get_detection_parameters = original_get_params
        
        return {
            'combination_index': combination_index,
            'params': current_params,
            'success': all_images_passed,
            'total_error': total_error,
            'results': current_results if all_images_passed else {},
            'failed_images': failed_images
        }
        
    except Exception as e:
        return {
            'combination_index': combination_index,
            'params': current_params,
            'success': False,
            'total_error': float('inf'),
            'results': {},
            'failed_images': [f"Process error: {str(e)[:50]}"]
        }


def run_sequential_optimization(test_images_path, param_grid):
    """Run optimization sequentially (single-threaded)."""
    print("Running SEQUENTIAL grid search for ruler detection parameter optimization...")
    
    all_param_combinations = list(itertools.product(*param_grid.values()))
    total_combinations = len(all_param_combinations)
    
    print(f"Testing {total_combinations:,} parameter combinations...")
    print("Parameter ranges:")
    for param, values in param_grid.items():
        if isinstance(values, range):
            print(f"  {param}: {values.start} to {values.stop-1} (step {values.step}) - {len(list(values))} values")
        else:
            print(f"  {param}: {values} - {len(values)} values")
    print("Expected measurements loaded from test_config.py")

    original_get_params = get_detection_parameters
    start_time = time.time()

    best_score = float('inf')
    best_params = {}
    best_results = {}
    successful_combinations = 0
    last_best_update = 0

    for i, combination in enumerate(all_param_combinations):
        current_params = dict(zip(['hough_threshold', 'hough_min_line_length', 'tick_min_height', 
                                  'canny_low_threshold', 'canny_high_threshold', 'roi_height_fraction'], combination))
        
        # More frequent progress updates for large grid
        if i % 100 == 0 or i < 20:
            elapsed = time.time() - start_time
            remaining_combinations = total_combinations - i
            if i > 0:
                avg_time_per_combination = elapsed / i
                estimated_remaining_time = avg_time_per_combination * remaining_combinations
                success_rate = (successful_combinations / i) * 100
                print(f"\nProgress: {i:,}/{total_combinations:,} ({i/total_combinations*100:.2f}%)")
                print(f"Elapsed: {elapsed/60:.1f}min - ETA: {estimated_remaining_time/60:.1f}min")
                print(f"Success rate: {success_rate:.1f}% - Best error: {best_score:.2f}px")
                print(f"Combinations since last improvement: {i - last_best_update}")
            else:
                print(f"\nStarting combination {i+1:,}/{total_combinations:,}")
            print(f"Current params: {current_params}")
        
        def mock_get_detection_parameters(museum_selection="Iraq Museum"):
            if museum_selection == "Iraq Museum (Sippar Library)":
                new_params = original_get_params("Iraq Museum (Sippar Library)").copy()
                # Update all parameters including roi_height_fraction
                new_params.update(current_params)
                return new_params
            return original_get_params(museum_selection)

        sys.modules['ruler_detector_iraq_museum'].get_detection_parameters = mock_get_detection_parameters

        total_error = 0
        all_images_passed = True
        failed_images = []
        current_results = {}
        
        for image_name, expected_data in EXPECTED_MEASUREMENTS.items():
            image_path = os.path.join(test_images_path, image_name)
            
            if not os.path.exists(image_path):
                print(f"  WARNING: Image not found: {image_name}")
                continue

            try:
                # Now properly pass the roi_height_fraction parameter
                detected_distance = detect_1cm_distance_iraq(
                    image_path, 
                    museum_selection="Iraq Museum (Sippar Library)",
                    roi_height_fraction=current_params['roi_height_fraction']
                )
                current_results[image_name] = detected_distance
                
                if detected_distance is None:
                    all_images_passed = False
                    failed_images.append(f"{image_name} (no detection)")
                    total_error = float('inf')
                    break
                elif not (expected_data['min'] <= detected_distance <= expected_data['max']):
                    all_images_passed = False
                    failed_images.append(f"{image_name} ({detected_distance}px outside range {expected_data['min']}-{expected_data['max']})")
                    total_error = float('inf')
                    break
                
                total_error += abs(detected_distance - expected_data['expected'])
                
            except Exception as e:
                all_images_passed = False
                failed_images.append(f"{image_name} (error: {str(e)[:30]})")
                total_error = float('inf')
                break
        
        if all_images_passed:
            successful_combinations += 1
            if total_error < best_score:
                best_score = total_error
                best_params = current_params
                best_results = current_results.copy()
                last_best_update = i
                print(f"  *** NEW BEST! Error: {best_score:.2f} px (combination {i+1:,})")
                print(f"      Parameters: {current_params}")
                
                # Show current best results
                print(f"      Results:")
                for img_name, detected in current_results.items():
                    expected = EXPECTED_MEASUREMENTS[img_name]['expected']
                    error = abs(detected - expected)
                    print(f"        {img_name}: {detected}px (expected {expected}px, error {error:.1f}px)")
            elif i < 20 or (i % 500 == 0):
                print(f"  SUCCESS: Error {total_error:.2f} px")
        elif i < 20 or i % 500 == 0:
            print(f"  Failed on: {failed_images[:2]}{'...' if len(failed_images) > 2 else ''}")

    # Restore the original function
    sys.modules['ruler_detector_iraq_museum'].get_detection_parameters = original_get_params

    return best_score, best_params, best_results, successful_combinations, total_combinations, time.time() - start_time


def run_parallel_optimization(test_images_path, param_grid, num_processes=None):
    """Run optimization in parallel using multiple processes."""
    print("Running PARALLEL grid search for ruler detection parameter optimization...")
    
    all_param_combinations = list(itertools.product(*param_grid.values()))
    total_combinations = len(all_param_combinations)
    
    if num_processes is None:
        num_processes = min(mp.cpu_count(), 8)
    
    print(f"Testing {total_combinations:,} parameter combinations using {num_processes} processes...")
    print(f"CPU cores available: {mp.cpu_count()}")
    print(f"Expected speedup: ~{num_processes}x faster than sequential")
    
    # Create arguments for parallel processing
    args_list = [(i, combination, test_images_path) 
                 for i, combination in enumerate(all_param_combinations)]
    
    best_score = float('inf')
    best_params = {}
    best_results = {}
    successful_combinations = 0
    
    start_time = time.time()
    
    try:
        with Pool(processes=num_processes) as pool:
            chunk_size = max(200, total_combinations // 30)  # Larger chunks for better performance
            
            for chunk_start in range(0, total_combinations, chunk_size):
                chunk_end = min(chunk_start + chunk_size, total_combinations)
                chunk_args = args_list[chunk_start:chunk_end]
                
                print(f"\nProcessing combinations {chunk_start:,} to {chunk_end:,} using {num_processes} processes...")
                chunk_start_time = time.time()
                
                # Process the chunk
                chunk_results = pool.map(test_parameter_combination, chunk_args)
                
                chunk_elapsed = time.time() - chunk_start_time
                combinations_in_chunk = len(chunk_args)
                print(f"Chunk completed in {chunk_elapsed/60:.1f} minutes ({combinations_in_chunk/chunk_elapsed:.1f} combinations/second)")
                
                # Process results from this chunk
                for result in chunk_results:
                    if result['success']:
                        successful_combinations += 1
                        if result['total_error'] < best_score:
                            best_score = result['total_error']
                            best_params = result['params'].copy()
                            best_results = result['results'].copy()
                            
                            print(f"*** NEW BEST! Error: {best_score:.2f} px (combination {result['combination_index']:,})")
                            print(f"    Parameters: {best_params}")
                
                # Progress update
                elapsed_time = time.time() - start_time
                combinations_processed = chunk_end
                remaining_combinations = total_combinations - combinations_processed
                
                if combinations_processed > 0:
                    avg_time_per_combination = elapsed_time / combinations_processed
                    estimated_remaining_time = avg_time_per_combination * remaining_combinations
                    success_rate = (successful_combinations / combinations_processed) * 100
                    
                    print(f"Progress: {combinations_processed:,}/{total_combinations:,} ({combinations_processed/total_combinations*100:.1f}%)")
                    print(f"Elapsed: {elapsed_time/60:.1f}min - ETA: {estimated_remaining_time/60:.1f}min")
                    print(f"Success rate: {success_rate:.1f}% - Successful: {successful_combinations:,}")
                    
                    if combinations_processed < total_combinations:
                        print(f"Processing speed: {combinations_processed/elapsed_time:.1f} combinations/second")
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Showing best results found so far...")
    except Exception as e:
        print(f"\nError during parallel processing: {e}")
        print("Showing best results found so far...")
    
    return best_score, best_params, best_results, successful_combinations, total_combinations, time.time() - start_time


class TestRulerDetectorIraqMuseum:
    """Test cases for Iraq Museum ruler detection functionality."""
    
    @pytest.fixture
    def test_images_path(self):
        """Get the path to the test images directory."""
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(script_dir, "Examples", "Sippar")
    
    @pytest.fixture
    def expected_measurements(self):
        """Expected measurements for test images with acceptable ranges."""
        return EXPECTED_MEASUREMENTS
    
    def test_detect_1cm_distance_all_images_sequential(self, test_images_path, expected_measurements):
        """Test ruler detection on all Sippar example images using sequential processing."""
        if not os.path.exists(test_images_path):
            pytest.skip(f"Test images directory not found: {test_images_path}")
        
        # Define the parameter space to search
        param_grid = {
            'hough_threshold': range(30, 140, 10),  # 11 values
            'hough_min_line_length': range(8, 40, 4),  # 8 values
            'tick_min_height': range(10, 40, 5),  # 6 values
            'canny_low_threshold': range(5, 30, 5),  # 5 values
            'canny_high_threshold': range(25, 70, 10),  # 5 values
            'roi_height_fraction': [0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75],  # 7 values
        }
        
        best_score, best_params, best_results, successful_combinations, total_combinations, elapsed_time = \
            run_sequential_optimization(test_images_path, param_grid)
        
        self._print_final_results(best_score, best_params, best_results, successful_combinations, 
                                 total_combinations, elapsed_time, expected_measurements, "SEQUENTIAL")
        
        assert best_params, "No parameter combination was found that passed all tests."
        assert best_score != float('inf')

    def test_detect_1cm_distance_all_images_parallel(self, test_images_path, expected_measurements):
        """Test ruler detection on all Sippar example images using parallel processing."""
        if not os.path.exists(test_images_path):
            pytest.skip(f"Test images directory not found: {test_images_path}")
        
        # Define the parameter space to search
        param_grid = {
            'hough_threshold': range(30, 140, 10),  # 11 values
            'hough_min_line_length': range(8, 40, 4),  # 8 values
            'tick_min_height': range(10, 40, 5),  # 6 values
            'canny_low_threshold': range(5, 30, 5),  # 5 values
            'canny_high_threshold': range(25, 70, 10),  # 5 values
            'roi_height_fraction': [0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75],  # 7 values
        }
        
        best_score, best_params, best_results, successful_combinations, total_combinations, elapsed_time = \
            run_parallel_optimization(test_images_path, param_grid)
        
        self._print_final_results(best_score, best_params, best_results, successful_combinations, 
                                 total_combinations, elapsed_time, expected_measurements, "PARALLEL")
        
        assert best_params, "No parameter combination was found that passed all tests."
        assert best_score != float('inf')

    def _print_final_results(self, best_score, best_params, best_results, successful_combinations, 
                            total_combinations, elapsed_time, expected_measurements, mode):
        """Print final optimization results."""
        print(f"\n{'='*80}")
        print(f"{mode} GRID SEARCH COMPLETE")
        print(f"{'='*80}")
        print(f"Total time elapsed: {elapsed_time/60:.1f} minutes ({elapsed_time/3600:.1f} hours)")
        print(f"Combinations tested: {total_combinations:,}")
        print(f"Average time per combination: {elapsed_time/total_combinations:.3f} seconds")
        print(f"Successful combinations: {successful_combinations:,}/{total_combinations:,} ({successful_combinations/total_combinations*100:.1f}%)")
        
        if best_params:
            print(f"\nBEST PARAMETERS FOUND:")
            print(f"{'='*50}")
            for param, value in best_params.items():
                print(f"  {param}: {value}")
            print(f"\nBest total error: {best_score:.2f} px")
            
            print(f"\nDETAILED RESULTS WITH BEST PARAMETERS:")
            print(f"{'='*60}")
            for image_name, detected_distance in best_results.items():
                expected = expected_measurements[image_name]['expected']
                error = abs(detected_distance - expected)
                print(f"{image_name}:")
                print(f"  Expected: {expected} px")
                print(f"  Detected: {detected_distance} px")
                print(f"  Error: {error:.2f} px")
                print()

    def test_detect_1cm_distance_single_image(self, test_images_path):
        """Test ruler detection on a single image (for quick testing)."""
        test_image = "IM.124625.H_02.JPG"
        image_path = os.path.join(test_images_path, test_image)
        
        if not os.path.exists(image_path):
            pytest.skip(f"Test image not found: {image_path}")

        detected_distance = detect_1cm_distance_iraq(image_path, museum_selection="Iraq Museum (Sippar Library)")

        assert detected_distance is not None, f"Failed to detect ruler in {test_image}"
        assert 650 <= detected_distance <= 750, (
            f"Detected distance {detected_distance} is outside acceptable range [650, 750]"
        )
        
        print(f"Single image test - {test_image}: {detected_distance} px")


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Ruler detection parameter optimization")
    parser.add_argument("--parallel", action="store_true", 
                       help="Use parallel processing (default: sequential)")
    parser.add_argument("--processes", type=int, default=None,
                       help="Number of processes to use (default: auto-detect, max 8)")
    parser.add_argument("--quick", action="store_true",
                       help="Use smaller parameter grid for quick testing")
    
    args = parser.parse_args()
    
    # Setup
    test_images_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Examples", "Sippar")
    
    if not os.path.exists(test_images_path):
        print(f"ERROR: Test images directory not found: {test_images_path}")
        sys.exit(1)
    
    print(f"Test images directory: {test_images_path}")
    
    # Define parameter grid
    if args.quick:
        # Smaller grid for quick testing
        param_grid = {
            'hough_threshold': range(40, 100, 20),  # 3 values
            'hough_min_line_length': range(12, 28, 8),  # 2 values
            'tick_min_height': range(15, 30, 10),  # 2 values
            'canny_low_threshold': range(5, 20, 10),  # 2 values
            'canny_high_threshold': range(30, 50, 10),  # 2 values
            'roi_height_fraction': [0.55, 0.60, 0.65],  # 3 values
        }
        # Total: 3 × 2 × 2 × 2 × 2 × 3 = 144 combinations
        print("Using QUICK parameter grid (144 combinations)")
    else:
        # Full comprehensive grid
        param_grid = {
            'hough_threshold': range(30, 140, 10),  # 11 values
            'hough_min_line_length': range(8, 40, 4),  # 8 values
            'tick_min_height': range(10, 40, 5),  # 6 values
            'canny_low_threshold': range(5, 30, 5),  # 5 values
            'canny_high_threshold': range(25, 70, 10),  # 5 values
            'roi_height_fraction': [0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75],  # 7 values
        }
        # Total: 11 × 8 × 6 × 5 × 5 × 7 = 92,400 combinations
        print("Using FULL parameter grid (92,400 combinations)")
    
    # Prevent multiprocessing issues on Windows
    if args.parallel:
        mp.freeze_support()
    
    # Run optimization
    if args.parallel:
        best_score, best_params, best_results, successful_combinations, total_combinations, elapsed_time = \
            run_parallel_optimization(test_images_path, param_grid, args.processes)
        mode = "PARALLEL"
    else:
        best_score, best_params, best_results, successful_combinations, total_combinations, elapsed_time = \
            run_sequential_optimization(test_images_path, param_grid)
        mode = "SEQUENTIAL"
    
    # Print final results
    print(f"\n{'='*80}")
    print(f"{mode} OPTIMIZATION COMPLETE")
    print(f"{'='*80}")
    print(f"Total time: {elapsed_time/60:.1f} minutes ({elapsed_time/3600:.1f} hours)")
    print(f"Average time per combination: {elapsed_time/total_combinations:.3f} seconds")
    print(f"Successful combinations: {successful_combinations:,}/{total_combinations:,} ({successful_combinations/total_combinations*100:.1f}%)")