import os
import sys
import pytest

# Add the lib directory to the path to import the module
script_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
lib_directory = os.path.join(script_directory, "lib")
if lib_directory not in sys.path:
    sys.path.insert(0, lib_directory)

from ruler_detector_iraq_museum import detect_1cm_distance_iraq


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
        return {
            "IM.124625.H_02.JPG": {"expected": 726, "min": 650, "max": 750},
            "IM.124625.K_02.JPG": {"expected": 716, "min": 650, "max": 750},
            "IM.124625.O_01.JPG": {"expected": 707, "min": 650, "max": 750}
        }
    
    def test_detect_1cm_distance_all_images(self, test_images_path, expected_measurements):
        """Test ruler detection on all Sippar example images."""
        if not os.path.exists(test_images_path):
            pytest.skip(f"Test images directory not found: {test_images_path}")
        
        results = {}
        
        for image_name, expected_data in expected_measurements.items():
            image_path = os.path.join(test_images_path, image_name)
            
            if not os.path.exists(image_path):
                pytest.skip(f"Test image not found: {image_path}")
            
            print(f"\nTesting image: {image_name}")
            print(f"Expected 1cm measurement: {expected_data['expected']} px")
            print(f"Acceptable range: {expected_data['min']}-{expected_data['max']} px")
            
            # Run the ruler detection with Sippar Library settings
            detected_distance = detect_1cm_distance_iraq(image_path, museum_selection="Iraq Museum (Sippar Library)")
            
            results[image_name] = detected_distance
            
            print(f"Detected 1cm measurement: {detected_distance}")
            
            # Assert that detection was successful
            assert detected_distance is not None, f"Failed to detect ruler in {image_name}"
            
            # Assert that the detected distance is within acceptable range
            assert expected_data['min'] <= detected_distance <= expected_data['max'], (
                f"Detected distance {detected_distance} for {image_name} is outside "
                f"acceptable range [{expected_data['min']}, {expected_data['max']}]"
            )
            
            print(f"PASS: {image_name} - detected {detected_distance} px")
        
        # Print summary
        print("\n" + "="*50)
        print("RULER DETECTION TEST SUMMARY")
        print("="*50)
        for image_name, detected_distance in results.items():
            expected = expected_measurements[image_name]['expected']
            difference = abs(detected_distance - expected)
            print(f"{image_name}:")
            print(f"  Expected: {expected} px")
            print(f"  Detected: {detected_distance} px")
            print(f"  Difference: {difference} px")
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
    
    def test_nonexistent_image(self):
        """Test behavior with non-existent image file."""
        fake_path = "nonexistent_image.jpg"
        result = detect_1cm_distance_iraq(fake_path, museum_selection="Iraq Museum (Sippar Library)")
        assert result is None, "Should return None for non-existent image"
    
    def test_invalid_museum_selection(self, test_images_path):
        """Test behavior with invalid museum selection."""
        test_image = "IM.124625.H_02.JPG"
        image_path = os.path.join(test_images_path, test_image)
        
        if not os.path.exists(image_path):
            pytest.skip(f"Test image not found: {image_path}")
        
        # Test with invalid museum selection
        result = detect_1cm_distance_iraq(image_path, museum_selection="Invalid Museum")
        # The function should still work or return None gracefully
        assert result is None or isinstance(result, (int, float))


if __name__ == "__main__":
    # Allow running the test directly
    test_images_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Examples", "Sippar")
    expected_measurements = {
        "IM.124625.H_02.JPG": {"expected": 726, "min": 650, "max": 750},
        "IM.124625.K_02.JPG": {"expected": 716, "min": 650, "max": 750},
        "IM.124625.O_01.JPG": {"expected": 707, "min": 650, "max": 750}
    }
    
    print("Running Sippar Library Ruler Detector Tests...")
    print("="*50)
    
    if not os.path.exists(test_images_path):
        print(f"ERROR: Test images directory not found: {test_images_path}")
        sys.exit(1)
    
    for image_name, expected_data in expected_measurements.items():
        image_path = os.path.join(test_images_path, image_name)
        
        if not os.path.exists(image_path):
            print(f"WARNING: Test image not found: {image_path}")
            continue
        
        print(f"\nTesting: {image_name}")
        print(f"Expected: {expected_data['expected']} px (range: {expected_data['min']}-{expected_data['max']})")
        
        detected_distance = detect_1cm_distance_iraq(image_path, museum_selection="Iraq Museum (Sippar Library)")
        
        if detected_distance is None:
            print(f"FAIL: No ruler detected in {image_name}")
        elif expected_data['min'] <= detected_distance <= expected_data['max']:
            difference = abs(detected_distance - expected_data['expected'])
            print(f"PASS: Detected {detected_distance} px (difference: {difference} px)")
        else:
            print(f"FAIL: Detected {detected_distance} px - outside acceptable range")