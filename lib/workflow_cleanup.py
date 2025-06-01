import os

def cleanup_intermediate_files(processed_subfolders, object_artifact_suffix, ruler_suffix="_ruler.tif"):
    """
    Remove intermediate processing files from each processed subfolder.

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
                    except Exception as e:
                        print(f"  Error removing {filename}: {e}")

            if files_removed > 0:
                print(f"  Removed {files_removed} intermediate files from {folder_name}")
                
        except Exception as e:
            print(f"  Error accessing folder {folder_name}: {e}")

    print(f"--- Cleanup complete: {total_removed} files removed ---")

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
            except Exception as e:
                print(f"  Warning: Could not remove temp file {file_path}: {e}")