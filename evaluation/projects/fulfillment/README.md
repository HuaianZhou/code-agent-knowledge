# Fulfillment export service

`exporter.write_batch` produces fulfillment batches. `recovery.write_recovery`
reconstructs the latest shipments from an event journal and exports a replacement.
Both accept an optional explicit format. `wire_formats` supports CSV v1 and JSONL
v2. Format support in this repository does not establish a receiver's deployment.
`inventory.summarize` computes SKU totals. Run `python -m unittest discover`.

This is a synthetic evaluation project, not a production service.
