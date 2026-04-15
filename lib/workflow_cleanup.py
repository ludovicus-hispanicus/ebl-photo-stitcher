import os
from hdr_processor import HDR_SUFFIX
from stitch_config import SCALED_RULER_FILE_SUFFIX
import shutil


def cleanup_intermediate_files(processed_subfolders, object_artifact_suffix, ruler_suffix=SCALED_RULER_FILE_SUFFIX):
    """
    Clean up intermediate files: replace originals with clean _object.tif versions,
    remove ruler and temp files.

    The _object.tif files (background-removed) replace the original source images.
    This is safe because the originals are already preserved in the source folder
    (the working folder contains copies).
    """
    print("\n--- Cleaning up intermediate files ---")
    total_removed = 0
    total_replaced = 0

    for subfolder_path in processed_subfolders:
        folder_name = os.path.basename(subfolder_path)

        try:
            # First pass: replace originals with _object.tif versions
            for filename in os.listdir(subfolder_path):
                if not filename.endswith(object_artifact_suffix):
                    continue

                object_path = os.path.join(subfolder_path, filename)
                # e.g., "Si.1_01_object.tif" -> base is "Si.1_01"
                base_name = filename[:-len(object_artifact_suffix)]

                # Find and remove the original source file (any extension)
                for orig_file in os.listdir(subfolder_path):
                    orig_name_no_ext = os.path.splitext(orig_file)[0]
                    if (orig_name_no_ext == base_name
                            and orig_file != filename
                            and not orig_file.endswith(object_artifact_suffix)
                            and not orig_file.endswith(ruler_suffix)
                            and not orig_file.endswith('.json')):
                        orig_path = os.path.join(subfolder_path, orig_file)
                        try:
                            os.remove(orig_path)
                            # Rename _object.tif to replace original (keep .tif extension)
                            new_name = base_name + '.tif'
                            new_path = os.path.join(subfolder_path, new_name)
                            os.rename(object_path, new_path)
                            total_replaced += 1
                            break
                        except Exception as e:
                            print(f"  Error replacing {orig_file}: {e}")

            # Second pass: remove ruler and temp files
            for filename in os.listdir(subfolder_path):
                file_path = os.path.join(subfolder_path, filename)
                if os.path.isfile(file_path) and (
                    filename.endswith(ruler_suffix)
                    or "temp_isolated_ruler" in filename
                    or "_rawscale.tif" in filename
                    or filename.endswith(object_artifact_suffix)  # any remaining _object.tif
                ):
                    try:
                        os.remove(file_path)
                        total_removed += 1
                    except Exception as e:
                        print(f"  Error removing {filename}: {e}")

        except Exception as e:
            print(f"  Error accessing folder {folder_name}: {e}")

    if processed_subfolders:
        main_folder = os.path.dirname(processed_subfolders[0])
        hdr_folders_removed = 0

        try:
            print(
                f"\n  Checking for HDR folders in main directory: {main_folder}")
            for item_name in os.listdir(main_folder):
                item_path = os.path.join(main_folder, item_name)
                if os.path.isdir(item_path) and item_name.endswith(HDR_SUFFIX):
                    try:
                        # Check for and preserve calculated_measurements.json before removing HDR folder
                        measurements_file = os.path.join(item_path, "calculated_measurements.json")
                        if os.path.exists(measurements_file):
                            # Extract base tablet ID (remove _HDR suffix)
                            base_tablet_id = item_name[:-len(HDR_SUFFIX)] if item_name.endswith(HDR_SUFFIX) else item_name
                            preserved_path = os.path.join(main_folder, f"{base_tablet_id}_measurements.json")
                            shutil.copy2(measurements_file, preserved_path)
                            print(f"    Preserved measurements: {base_tablet_id}_measurements.json")
                        
                        shutil.rmtree(item_path)
                        hdr_folders_removed += 1
                        total_removed += 1
                        print(f"    Removed HDR folder: {item_name}")
                    except Exception as e:
                        print(f"  Error removing HDR folder {item_name}: {e}")

            if hdr_folders_removed > 0:
                print(
                    f"  Removed {hdr_folders_removed} HDR folders from main directory")

        except Exception as e:
            print(f"  Error accessing main directory {main_folder}: {e}")

    if total_replaced > 0:
        print(f"  Replaced {total_replaced} original(s) with clean background-removed versions")
    print(f"--- Cleanup complete: {total_replaced} replaced, {total_removed} files/folders removed ---")


def normalize_subfolder_names(processed_subfolders):
    """
    Normalize subfolder names by replacing spaces with dots.
    E.g., 'Si 10' -> 'Si.10'
    """
    import re
    renamed_count = 0

    for subfolder_path in processed_subfolders:
        folder_name = os.path.basename(subfolder_path)
        # Replace spaces between a prefix and number with a dot
        normalized = re.sub(r'(\w+)\s+(\d+)', r'\1.\2', folder_name)

        if normalized != folder_name:
            new_path = os.path.join(os.path.dirname(subfolder_path), normalized)
            if not os.path.exists(new_path):
                try:
                    os.rename(subfolder_path, new_path)
                    renamed_count += 1
                except OSError as e:
                    print(f"  Warning: Could not rename folder '{folder_name}' to '{normalized}': {e}")

    if renamed_count > 0:
        print(f"  Normalized {renamed_count} folder name(s) (spaces -> dots)")


def cleanup_temp_files(*file_paths):
    """
    Clean up temporary files if they exist.

    Args:
        *file_paths: Variable number of file paths to clean up
    """
    for file_path in file_paths:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"    Removed temp file: {os.path.basename(file_path)}")
            except Exception as e:
                print(
                    f"  Warning: Could not remove temp file {file_path}: {e}")
