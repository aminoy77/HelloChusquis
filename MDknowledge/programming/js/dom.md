# JavaScript DOM

- In JavaScript, `document.querySelector('.cls')` finds the first match; `querySelectorAll` finds all.
- In JavaScript, `getElementById` is fastest for single ids; prefer querySelector for consistency.
- In JavaScript, `el.textContent` sets safe text while `innerHTML` parses HTML (XSS risk with user data).
- In JavaScript, `document.createElement` plus `appendChild` builds nodes without reparsing markup.
- In JavaScript, `el.classList.add/remove/toggle` manipulates classes without string surgery.
- In JavaScript, `el.setAttribute`/`dataset` read and write attributes and `data-*` state.
- In JavaScript, batch DOM writes and read layout once to avoid forced reflow thrash.
- In JavaScript, `addEventListener` attaches handlers; inline `onclick` attributes mix concerns.
- In JavaScript, `documentFragment` groups multi-node inserts into a single reflow.
- In JavaScript, `el.remove()` detaches nodes; dropping references lets GC reclaim them.
