# HTML basics

- In HTML, `<!DOCTYPE html>` triggers standards mode; every page starts with it plus `<html lang="en">`.
- In HTML, `<head>` holds metadata (`<title>`, `<meta charset="utf-8">`, stylesheets) while `<body>` holds visible content.
- In HTML, headings run `<h1>` (one per page) down to `<h6>` for document outline and accessibility.
- In HTML, `<p>` paragraphs, `<a href="...">` links, and `<img src alt>` images are the core content tags.
- In HTML, `alt` text on images describes content for screen readers; leave it empty only for decoration.
- In HTML, semantic tags (`<header>`, `<nav>`, `<main>`, `<article>`, `<footer>`) beat generic `<div>` for structure.
- In HTML, `<ul>`/`<ol>` with `<li>` mark unordered and ordered lists; nesting lists needs `<li>` wrappers.
- In HTML, `<form action method>` groups inputs; each input needs a `<label>` for accessibility.
- In HTML, input types (`email`, `number`, `date`, `checkbox`) give free validation and mobile keyboards.
- In HTML, `required`, `minlength`, `pattern`, `min`/`max` validate natively before JavaScript runs.
- In HTML, `<button type="submit">` submits forms while `type="button"` is inert for scripts.
- In HTML, `id` must be unique per page; `class` groups elements for styling and scripting.
- In HTML, `data-*` attributes store custom per-element state readable via `dataset`.
- In HTML, `&amp;`, `&lt;`, `&gt;`, `&quot;` escape special characters in text content.
- In HTML, `<meta name="viewport" content="width=device-width, initial-scale=1">` enables mobile layouts.
- In HTML, `<script src="app.js" defer>` loads JavaScript after parsing without blocking render.
- In HTML, `<link rel="stylesheet" href="style.css">` attaches external CSS in document order.
- In HTML, validate markup early; unclosed tags produce unpredictable layouts across browsers.
