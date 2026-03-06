from typing import Dict, Iterable, Optional, Tuple


# Day-of-year windows are approximate agronomic guidance bands and are kept
# intentionally conservative to avoid overfitting to a single locality.
# The mapping is model-crop-name -> (start_doy, end_doy).
PAKISTAN_CROP_WINDOW_BY_MODEL: Dict[str, Tuple[int, int]] = {
    # Maize (kharif/monsoon sowing window, mid-Jun to mid-Jul)
    # Used for corn aliases available in GenericCrops_final.crop.
    "CornRM.90": (166, 196),
    "CornRM.100": (166, 196),
    "CornRM.110": (166, 196),
    "CornSilageRM.90": (166, 196),
    "CornSilageRM.100": (166, 196),
    "CornSilageRM.110": (166, 196),
    # Wheat (rabi sowing window, Nov 1 to Nov 30)
    "WinterWheat": (305, 334),
}


PAKISTAN_CROP_CALENDAR_SOURCES = [
    {
        "name": "KP Agriculture - Maize Production Technology",
        "url": "https://zarat.kp.gov.pk/assets/uploads/publications/Maize%20Production%20Technology.pdf",
        "notes": "Used for maize seasonal sowing guidance (kharif/monsoon window support).",
    },
    {
        "name": "PBS - Approved Crop Calendar (Kharif)",
        "url": "https://www.pbs.gov.pk/sites/default/files//tables/table_13_approved_crop_calendar_kharif.pdf",
        "notes": "Used as official season reference for kharif crops.",
    },
    {
        "name": "PBS - Approved Crop Calendar (Rabi)",
        "url": "https://www.pbs.gov.pk/sites/default/files/tables/table_14_approved_crop_calendar_rabi.pdf",
        "notes": "Used as official season reference for rabi crops.",
    },
]


def get_calendar_windows_for_crops(
    crops: Iterable[str],
    window_map: Optional[Dict[str, Tuple[int, int]]] = None,
) -> Dict[str, Tuple[int, int]]:
    """
    Return only the known Pakistan calendar windows for the requested crop list.

    Unknown crops are intentionally ignored so callers can keep backward
    compatibility and fall back to existing action mapping.
    """
    mapping = PAKISTAN_CROP_WINDOW_BY_MODEL if window_map is None else window_map
    out: Dict[str, Tuple[int, int]] = {}
    for crop in crops:
        if crop in mapping:
            out[crop] = mapping[crop]
    return out
