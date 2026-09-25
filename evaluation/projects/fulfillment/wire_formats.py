"""Supported interchange formats; deployments choose which to use."""
import csv
import json


def encode(records, stream, format_name):
    if format_name == "csv-v1":
        writer = csv.DictWriter(stream, fieldnames=["id", "sku", "quantity"])
        writer.writeheader()
        for record in records:
            writer.writerow({key: record[key] for key in writer.fieldnames})
    elif format_name == "jsonl-v2":
        for record in records:
            stream.write(json.dumps({"version": 2, **record}) + "\n")
    else:
        raise ValueError("Unsupported format: " + format_name)


def decode(stream, format_name):
    if format_name == "csv-v1":
        return [{**row, "quantity": int(row["quantity"])} for row in csv.DictReader(stream)]
    if format_name == "jsonl-v2":
        return [{key: value for key, value in json.loads(line).items() if key != "version"}
                for line in stream if line.strip()]
    raise ValueError("Unsupported format: " + format_name)
