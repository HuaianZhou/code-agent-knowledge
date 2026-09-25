from wire_formats import encode


def replay_events(events):
    """Latest upsert wins; deletion removes a shipment from the recovery image."""
    shipments = {}
    for event in events:
        if event["op"] == "delete":
            shipments.pop(event["id"], None)
        elif event["op"] == "upsert":
            shipments[event["id"]] = {key: event[key] for key in ("id", "sku", "quantity")}
        else:
            raise ValueError("Unknown event operation")
    return list(shipments.values())


def write_recovery(site, events, stream, format_name="csv-v1"):
    """Export a replacement batch after reconstructing the journal."""
    encode(replay_events(events), stream, format_name)
