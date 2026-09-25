from wire_formats import encode


def write_batch(site, records, stream, format_name="csv-v1"):
    """Write a site's fulfillment batch. An explicit format overrides the default."""
    encode(list(records), stream, format_name)
