"""CS2 event macro-region identity codes; unknown hosts have no region."""

REGION_CODES = ("EU", "CIS", "NA", "SA", "AS", "OCE", "AF")


def macro_region(code):
    return code if code in REGION_CODES else None
