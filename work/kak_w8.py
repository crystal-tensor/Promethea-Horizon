import json, pathlib, numpy as np, sympy as sp
from scipy.linalg import sqrtm

# Load w8_21 matrix
p = pathlib.Path(r"C:\Users\jack9\Documents\Codex\2026-06-26\crystal-tensor-axiom-horizon-https-github\repo\results\B7_nonlocal_template_block_scan_v0.json")
d = json.loads(p.read_text("utf-8"))
templates = d.get("templates", d.get("template_certificates", []))

w8 = None
for t in templates:
    if "w8_21" in t.get("template_id", ""):
        m = t.get("matrix")
        if m and isinstance(m, list) and isinstance(m[0], list):
            w8 = np.array(m, dtype=complex)
            break

if w8 is None:
    print("w8_21 matrix not found in template data")
    quit()

print("w8_21 matrix shape:", w8.shape)
print("Is unitary:", np.allclose(w8 @ w8.conj().T, np.eye(w8.shape[0]), atol=1e-10))

# KAK decomposition via magic basis
# The magic basis transforms the two-qubit unitary into an orthogonal matrix
# whose eigenvalues reveal the KAK coordinates
magic = np.array([
    [1, 0, 0, 1j],
    [0, 1j, 1, 0],
    [0, 1j, -1, 0],
    [1, 0, 0, -1j]
], dtype=complex) / np.sqrt(2)

magic_dag = magic.conj().T
Um = magic_dag @ w8 @ magic

# Um should be real orthogonal (up to global phase)
# Remove global phase
det = np.linalg.det(Um)
phase = det ** (1/4)
Um_norm = Um / phase

print("Um is real:", np.allclose(Um_norm.imag, 0, atol=1e-10))
Um_real = Um_norm.real

# The KAK coordinates are derived from the eigenvalues of Um^T Um
M = Um_real.T @ Um_real
eigenvalues = np.linalg.eigvals(M)
print("Eigenvalues of M:", eigenvalues[:4])

# The canonical KAK coordinates are log eigenvalues divided by 2i
eigenvalues_sorted = sorted([abs(ev) for ev in eigenvalues[:4]])
print("Eigenvalue magnitudes:", eigenvalues_sorted)

# KAK coordinates in canonical order
cx = np.arctan2(np.sqrt(np.abs(eigenvalues[0])), 1.0)  # approximation
print("Raw eigenvalues:", eigenvalues)
