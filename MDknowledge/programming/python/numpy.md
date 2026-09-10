# Python NumPy

- NumPy arrays vectorize math: `a + b` beats Python loops by orders of magnitude.
- `np.zeros/ones/arange/linspace` construct ranges without loops.
- Broadcasting aligns mismatched shapes by stretching size-1 axes automatically.
- `a.reshape/mask/boolean-index` restructure and filter without copies where possible.
- Reductions (`sum/mean/max(axis=0)`) collapse dimensions selectively.
- `np.random.default_rng(seed)` generators supersede legacy global RandomState.
- Views share memory with parents; `.copy()` severs the link deliberately.
- Dtypes (`float64` vs `float32`) trade precision against memory and speed.
- `np.loadtxt/genfromtxt` ingest CSVs; `np.save/load` persist arrays natively.
- Pandas builds labeled frames atop NumPy's raw speed.
