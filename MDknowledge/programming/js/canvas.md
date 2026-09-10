# Canvas basics

- `<canvas>` plus `getContext('2d')` unlocks immediate-mode drawing.
- Set `width/height` attributes (not just CSS) for crisp resolution.
- Paths (`beginPath/moveTo/lineTo/stroke`) draw shapes incrementally.
- `requestAnimationFrame` syncs animation loops to display refresh.
- Device-pixel-ratio scaling (`canvas.width = cssW * dpr`) sharpens retina output.
- Offscreen canvases pre-render static layers for frame-rate wins.
- `toDataURL` exports snapshots for downloads and thumbnails.
- Hit-testing is manual: track shapes to map clicks yourself.
- WebGL contexts (`webgl2`) graduate to GPU 3D when 2D limits hit.
- Clear (`clearRect`) each frame or trails smear intentionally.
