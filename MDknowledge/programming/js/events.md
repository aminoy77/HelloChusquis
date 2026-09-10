# JavaScript events

- In JavaScript, events bubble from target up to document; `stopPropagation()` halts the climb.
- In JavaScript, `addEventListener(type, fn, {once: true})` auto-removes one-shot handlers.
- In JavaScript, delegate dynamic lists: one parent listener reading `event.target` beats per-item handlers.
- In JavaScript, `preventDefault()` cancels native behavior like form submits and link navigation.
- In JavaScript, `input` fires on every keystroke while `change` fires on commit (blur/enter).
- In JavaScript, `event.target` is the origin element; `event.currentTarget` is the attached one.
- In JavaScript, `{passive: true}` on touch/wheel listeners keeps scrolling smooth.
- In JavaScript, `removeEventListener` needs the identical function reference used at attach time.
- In JavaScript, `CustomEvent` with `detail` payloads decouples components cleanly.
- In JavaScript, debounce rapid events (resize, typing) and throttle continuous ones (scroll).
