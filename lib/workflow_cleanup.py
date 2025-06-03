import os
from hdr_processor import HDR_SUFFIX
import shutil


def cleanup_intermediate_files(processed_subfolders, object_artifact_suffix, ruler_suffix="_ruler.tif"):
    """
    Remove intermediate processing files from each processed subfolder and HDR folders from main directory.

    Args:
        processed_subfolders: List of subfolder paths that were processed
        object_artifact_suffix: Suffix used for extracted object files (e.g., "_object.tif")
        ruler_suffix: Suffix used for ruler files (default: "_ruler.tif")
    """
    print("\n--- Cleaning up intermediate files ---")
    total_removed = 0

    for subfolder_path in processed_subfolders:
        folder_name = os.path.basename(subfolder_path)
        files_removed = 0

        try:
            for filename in os.listdir(subfolder_path):
                file_path = os.path.join(subfolder_path, filename)
                if os.path.isfile(file_path) and (
                    filename.endswith(object_artifact_suffix)
                    or filename.endswith(ruler_suffix)
                    or "temp_isolated_ruler" in filename
                    or "_rawscale.tif" in filename
                ):
                    try:
                        os.remove(file_path)
                        files_removed += 1
                        total_removed += 1
                        print(f"    Removed file: {filename}")
                    except Exception as e:
                        print(f"  Error removing {filename}: {e}")

            if files_removed > 0:
                print(
                    f"  Removed {files_removed} intermediate files from {folder_name}")

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

    print(f"--- Cleanup complete: {total_removed} files/folders removed ---")


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
