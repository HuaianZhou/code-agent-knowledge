def summarize(records):
    """Return quantity totals by SKU."""
    totals = {}
    for record in records:
        totals[record["sku"]] = record["quantity"]
    return totals
