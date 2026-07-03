import json, pathlib, numpy as np
p = pathlib.Path(r"C:\Users\jack9\Documents\Codex\2026-06-26\crystal-tensor-axiom-horizon-https-github\repo\results\B7_nonlocal_template_block_scan_v0.json")
d = json.loads(p.read_text("utf-8"))
templates = d.get("templates", d.get("template_certificates", []))
for t in templates:
    tid = t.get("template_id", "")
    if "w8_21" in tid:
        print("Found:", tid)
        if "matrix" in t:
            m = t["matrix"]
            if isinstance(m, list) and isinstance(m[0], list):
                print("Shape:", len(m), "x", len(m[0]))
        print("Keys:", list(t.keys())[:10])
        break
