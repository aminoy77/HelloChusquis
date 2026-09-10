# Python matplotlib

- `plt.plot(x, y)` draws lines; `scatter/bar/hist` cover points, counts, distributions.
- Figures hold axes; `subplots()` grids multiple views in one image.
- Labels, titles, and legends (`plt.legend()`) make plots self-explanatory.
- `plt.savefig('fig.png', dpi=150, bbox_inches='tight')` exports publication-ready files.
- Stylesheets (`plt.style.use('seaborn-v0_8')`) theme consistently in one line.
- Twin axes (`twinx`) overlay different units without distortion.
- Annotations (`annotate` with arrows) narrate key points directly.
- Log scales (`set_xscale('log')`) reveal exponential relationships linearly.
- Seaborn builds statistical plots (heatmaps, violins) atop matplotlib.
- Interactive backends (`%matplotlib widget`) explore inside notebooks.
