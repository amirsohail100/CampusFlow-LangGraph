# data/

Put your two source PDFs here, named exactly:

- `academics_handbook.pdf`
- `fee_structure.pdf`

`tools/nodes.py` loads them lazily the first time a question is routed to
the academic or fee path, so the server will start fine without them —
you'll just get a clear error on the first relevant question until they're
added.
