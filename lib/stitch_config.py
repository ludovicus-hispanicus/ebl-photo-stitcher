# Configuration for the stitching process - use consistent patterns

# File naming conventions - define these first to avoid circular imports
OBJECT_FILE_SUFFIX = "_object.tif"
SCALED_RULER_FILE_SUFFIX = "_ruler.tif"
FINAL_TIFF_SUBFOLDER_NAME = "_Final_TIFF"
FINAL_JPG_SUBFOLDER_NAME = "_Final_JPG"

# Base patterns without file extension separator
STITCH_VIEW_PATTERNS_BASE = { 
    "obverse": "_01", 
    "reverse": "_02", 
    "bottom": "_04", 
    "top": "_03", 
    "right": "_06", 
    "left": "_05", 
    "ruler": "" 
}

# For detecting original files - include file extension separator
STITCH_VIEW_PATTERNS_WITH_EXT = {k: f"{v}." for k, v in STITCH_VIEW_PATTERNS_BASE.items()}

# For detecting processed object files
STITCH_VIEW_PATTERNS_FOR_OBJECTS = {k: f"{v}{OBJECT_FILE_SUFFIX}" for k, v in STITCH_VIEW_PATTERNS_BASE.items() if k != "ruler"}

# Intermediate image suffixes - for detecting both original and object files
INTERMEDIATE_SUFFIX_BASE = {
    "ot": "intermediate_obverse_top",
    "ob": "intermediate_obverse_bottom",
    "ol": "intermediate_obverse_left",
    "or": "intermediate_obverse_right",
    "rt": "intermediate_reverse_top",
    "rb": "intermediate_reverse_bottom",
    "rl": "intermediate_reverse_left",
    "rr": "intermediate_reverse_right"
}

INTERMEDIATE_SUFFIX_WITH_EXT = {k: f"_{k}." for k in INTERMEDIATE_SUFFIX_BASE.keys()}
INTERMEDIATE_SUFFIX_FOR_OBJECTS = {k: f"_{k}{OBJECT_FILE_SUFFIX}" for k in INTERMEDIATE_SUFFIX_BASE.keys()}

# Relationships between intermediates and main views
INTERMEDIATE_VIEW_RELATIONSHIPS = {
    "intermediate_obverse_top": ("obverse", "top"),
    "intermediate_obverse_bottom": ("obverse", "bottom"),
    "intermediate_obverse_left": ("obverse", "left"),
    "intermediate_obverse_right": ("obverse", "right"),
    "intermediate_reverse_top": ("reverse", "top"),
    "intermediate_reverse_bottom": ("reverse", "bottom"),
    "intermediate_reverse_left": ("reverse", "left"),
    "intermediate_reverse_right": ("reverse", "right")
}

# Layout parameters
STITCH_VIEW_GAP_PX = 100 
STITCH_RULER_PADDING_PX = 100
STITCH_FINAL_MARGIN_PX = 100

# Logo settings
STITCH_LOGO_MAX_WIDTH_FRACTION = 0.70
STITCH_LOGO_PADDING_ABOVE = 30
STITCH_LOGO_PADDING_BELOW = 30

# Image settings
STITCH_OUTPUT_DPI = 600
STITCH_BACKGROUND_COLOR = (0, 0, 0)
STITCH_TIFF_COMPRESSION = "lzw"
JPEG_SAVE_QUALITY = 85

# Museum configurations
MUSEUM_CONFIGS = {
    "British Museum": {
        "background_color": (0, 0, 0),  # Black
        "ruler_type": "tif",
        "ruler_templates": {
            "1cm": "BM_1cm_scale.tif",
            "2cm": "BM_2cm_scale.tif", 
            "5cm": "BM_5cm_scale.tif"
        }
    },
    "Iraq Museum": {
        "background_color": (255, 255, 255),  # White
        "ruler_type": "svg",
        "ruler_template": "IM_photo_ruler.svg",
        "ruler_size_cm": 4.599
    },
    "eBL Ruler (CBS)": {
        "background_color": (255, 255, 255),  # White
        "ruler_type": "svg",
        "ruler_template": "General_eBL_photo_ruler.svg",
        "ruler_size_cm": 4.317
    },
    "Non-eBL Ruler (VAM)": {
        "background_color": (255, 255, 255),  # White
        "ruler_type": "svg",
        "ruler_template": "General_External_photo_ruler.svg",
        "ruler_size_cm": 3.248
    }
}

# Metadata defaults
STITCH_INSTITUTION = "LMU Munich"
STITCH_CREDIT_LINE = "The image was produced with funding from the European Research Council (ERC) under the European Union's Horizon Europe research and innovation programme (Grant agreement No. 101171038). Grant Acronym RECC (DOI: 10.3030/101171038). Published under a CC BY NC 4.0 license."
STITCH_XMP_USAGE_TERMS = f"Published under a CC BY NC 4.0 license."
