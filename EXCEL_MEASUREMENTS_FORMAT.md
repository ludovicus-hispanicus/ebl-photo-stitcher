# Custom Measurements Excel Format

## Overview

The eBL Photo Stitcher now supports uploading custom tablet width measurements via Excel files. This feature allows you to provide your own width measurements for tablets, which will be used as a fallback when the ruler recognition system cannot determine the scale from the image.

## Excel File Format

### Requirements
- Excel file (.xlsx or .xls)
- Minimum 2 columns
- First column: Tablet ID (e.g., "BM.12345", "BM.58103")
- Second column: Width measurement value in centimeters

### Example Excel Structure

| Tablet ID | Width (cm) |
|-----------|------------|
| BM.12345  | 8.5        |
| BM.58103  | 12.3       |
| BM.67890  | 6.7        |

## Usage Instructions

1. **Prepare your Excel file** following the format above
2. **Open eBL Photo Stitcher** and go to the "Advanced (Ruler)" tab
3. **Click "Browse..."** in the "Custom Tablet Measurements" section
4. **Select your Excel file** - the system will validate and load it
5. **Check the status** - a green checkmark indicates successful loading
6. **Run your workflow** - custom measurements will be used when available

## Priority Order

The system uses measurements in this priority order:
1. **Ruler recognition** from the photograph (highest priority)
2. **Custom Excel measurements** (your uploaded file)
3. **Built-in database** measurements (lowest priority)

## Important Notes

- Measurements must be width values in centimeters
- Tablet IDs are matched flexibly (e.g., "12345" will match "BM.12345")
- Invalid rows (non-numeric values, empty cells) are automatically skipped
- The file path is saved with your settings and will be reloaded when you restart the application

## Troubleshooting

- **"Invalid Excel file"**: Ensure your file has at least 2 columns with valid data
- **"No valid measurements found"**: Check that your width values are numeric and positive
- **"Error loading file"**: Verify the file isn't corrupted and is a valid Excel format

## Technical Details

- Supported formats: .xlsx, .xls
- Required Python packages: pandas, openpyxl
- The system merges your custom measurements with the built-in database
- Custom measurements take precedence over built-in ones for matching tablet IDs
