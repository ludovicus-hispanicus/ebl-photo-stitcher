"""Museum-specific settings for the eBL Photo Stitcher."""

try:
    import project_manager
except ImportError:
    project_manager = None


class MuseumOptionsManager:
    """Manager for museum-specific options and settings."""

    @staticmethod
    def configure_museum_settings(museum_selection, stitch_config, original_credit, original_institution):
        """Configure stitching metadata from the active project or legacy museum mapping."""

        # Prefer active project metadata
        active = project_manager.get_active_project() if project_manager else None
        if active is not None and active.get("name") == museum_selection:
            credit = active.get("credit_line", "") or ""
            institution = active.get("institution", "") or ""
            stitch_config.STITCH_CREDIT_LINE = credit if credit else original_credit
            stitch_config.STITCH_INSTITUTION = institution if institution else original_institution
            return

        # Legacy fallback (no active project matched)
        if museum_selection == "Iraq Museum":
            stitch_config.STITCH_CREDIT_LINE = (
                "Cuneiform Artefacts of Iraq in Context (CAIC), "
                "Bayerische Akademie der Wissenschaften"
            )
        elif museum_selection == "Iraq Museum (Sippar Library)":
            stitch_config.STITCH_CREDIT_LINE = (
                "College of Arts, University of Baghdad"
            )
        elif museum_selection == "Non-eBL Ruler (VAM)":
            stitch_config.STITCH_CREDIT_LINE = ""
        else:
            stitch_config.STITCH_CREDIT_LINE = original_credit

        if museum_selection == "Iraq Museum":
            stitch_config.STITCH_INSTITUTION = "The Iraq Museum – eBL Project"
        elif museum_selection == "Iraq Museum (Sippar Library)":
            stitch_config.STITCH_INSTITUTION = "University of Baghdad"
        elif museum_selection == "Non-eBL Ruler (VAM)":
            stitch_config.STITCH_INSTITUTION = (
                "Staatliche Museen zu Berlin, Vorderasiatisches Museum"
            )
        else:
            stitch_config.STITCH_INSTITUTION = original_institution
