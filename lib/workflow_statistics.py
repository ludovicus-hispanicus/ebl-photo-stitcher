import re
import time


def print_final_statistics(start_time, total_ok, total_err, cr2_conv_total, failed_objects):
    """Print final processing statistics."""
    print(
        f"\n--- Processing Complete ---\nRAW converted: {cr2_conv_total}\nSets OK: {total_ok}\nSets Error: {total_err}\n")

    end_time = time.time()
    elapsed_seconds = end_time - start_time
    minutes, seconds = divmod(elapsed_seconds, 60)

    avg_seconds = elapsed_seconds / total_ok if total_ok > 0 else 0
    avg_minutes, avg_seconds = divmod(avg_seconds, 60)

    print(f"\n--- Processing Statistics ---")
    print(f"Time elapsed: {int(minutes):02d} m {int(seconds):02d} s")
    print(f"Objects processed: {total_ok}")

    if total_err > 0:
        cleaned_failed_objects = []
        for obj in failed_objects:
            base_name = re.sub(r'_\d+$', '', obj)
            if base_name not in cleaned_failed_objects:
                cleaned_failed_objects.append(base_name)

        print(f"Objects that could not be processed ({total_err}):")
        for obj_name in cleaned_failed_objects:
            print(f"  - {obj_name}")

    print(f"Average time per object: {int(avg_minutes):02d} m {int(avg_seconds):02d} s")
