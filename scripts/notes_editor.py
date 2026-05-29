#!/usr/bin/env python3

from __future__ import annotations

import argparse
import html
import json
import mimetypes
import os
import re
import sys
import threading
import time
import unicodedata
import uuid
import webbrowser
from datetime import date, datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "notes-data"
DATA_FILE = DATA_DIR / "notes.json"
NOTES_DIR = ROOT / "notes"
GENERATED_MARKER = "<!-- generated-by-notes-editor -->"
DEFAULT_LEDE = "My notes, thoughts, and rambles should appear here."


SITE_CSS = r"""
    :root {
      --bg: #f4f7f4;
      --text: #191b18;
      --muted: #687069;
      --accent: #517783;
      --rule: #d7ded8;
      --bg-dark: #101411;
      --text-dark: #ecefe8;
      --muted-dark: #a7ada4;
      --accent-dark: #98b8c2;
      --rule-dark: #2c352f;
    }

    *, *::before, *::after {
      box-sizing: border-box;
    }

    html {
      color-scheme: light;
    }

    body {
      margin: 0;
      min-height: 100vh;
      background: var(--bg);
      color: var(--text);
      font-family: "Source Serif 4", Georgia, "Times New Roman", serif;
      font-size: 18px;
      line-height: 1.7;
      -webkit-font-smoothing: antialiased;
      text-rendering: optimizeLegibility;
      transition: background-color 0.25s ease, color 0.25s ease;
    }

    body.dark {
      color-scheme: dark;
      --bg: var(--bg-dark);
      --text: var(--text-dark);
      --muted: var(--muted-dark);
      --accent: var(--accent-dark);
      --rule: var(--rule-dark);
    }

    ::selection {
      background: rgba(81, 119, 131, 0.2);
    }

    p {
      margin: 0;
    }

    a {
      color: inherit;
      text-decoration: underline;
      text-decoration-color: var(--accent);
      text-decoration-thickness: 0.06em;
      text-underline-offset: 0.18em;
      transition: color 0.2s ease, text-decoration-color 0.2s ease;
    }

    a:hover {
      color: var(--accent);
    }

    a:focus-visible {
      outline: 1px solid var(--accent);
      outline-offset: 4px;
    }

    h1, h2, h3 {
      margin: 0;
      color: var(--text);
      font-family: inherit;
      font-weight: 500;
      letter-spacing: 0;
    }

    .theme-toggle {
      position: fixed;
      top: 1.25rem;
      right: 1.25rem;
      z-index: 10;
      display: grid;
      place-items: center;
      width: 2.25rem;
      height: 2.25rem;
      padding: 0;
      border: 0;
      background: transparent;
      color: var(--muted);
      cursor: pointer;
      font: inherit;
      font-size: 1.2rem;
      line-height: 1;
      transition: color 0.2s ease, transform 0.2s ease;
    }

    .theme-toggle:hover {
      color: var(--accent);
      transform: rotate(12deg);
    }

    .theme-toggle:focus-visible {
      outline: 0;
      color: var(--accent);
      text-decoration: underline;
      text-underline-offset: 0.2em;
    }

    .page {
      max-width: 1040px;
      margin: 0 auto;
      padding: 5.5rem 2rem 4rem;
    }

    .topline {
      display: flex;
      gap: 1.25rem;
      margin-bottom: 5rem;
      color: var(--muted);
      font-size: 1rem;
      line-height: 1.4;
    }

    .topline a {
      color: var(--text);
      text-decoration: none;
    }

    .topline a:hover {
      color: var(--accent);
      text-decoration: underline;
      text-decoration-color: var(--accent);
    }

    header {
      max-width: 760px;
      margin-bottom: 4.5rem;
    }

    h1 {
      font-size: 4.75rem;
      line-height: 0.95;
    }

    .lede {
      max-width: 38rem;
      margin-top: 1.15rem;
      color: var(--muted);
      font-size: 1.35rem;
      line-height: 1.45;
    }

    section {
      display: grid;
      grid-template-columns: 11rem minmax(0, 1fr);
      gap: 2rem 4rem;
      padding: 3.75rem 0;
      border-top: 1px solid var(--rule);
    }

    section > h2 {
      grid-column: 1;
      margin-top: 0.25rem;
      color: var(--muted);
      font-size: 1.05rem;
      line-height: 1.4;
    }

    section > :not(h2) {
      grid-column: 2;
    }

    .note-list {
      list-style: none;
      margin: 0;
      padding: 0;
    }

    .note-list li {
      padding: 1.35rem 0;
      border-top: 1px solid var(--rule);
    }

    .note-list li:first-child {
      padding-top: 0;
      border-top: 0;
    }

    .note-title {
      display: inline-block;
      color: var(--text);
      font-size: 1.2rem;
      font-weight: 600;
      line-height: 1.35;
      text-decoration: none;
    }

    .note-title:hover {
      color: var(--accent);
      text-decoration: underline;
      text-decoration-color: var(--accent);
    }

    .note-meta {
      display: block;
      margin-top: 0.35rem;
      color: var(--muted);
      font-size: 1rem;
      line-height: 1.45;
    }

    .empty-note {
      max-width: 38rem;
      color: var(--muted);
      font-size: 1.1rem;
      line-height: 1.65;
    }

    .note-article {
      max-width: 720px;
    }

    .note-article h2,
    .note-article h3 {
      margin: 2.4rem 0 0.8rem;
      line-height: 1.25;
    }

    .note-article h2 {
      font-size: 1.6rem;
    }

    .note-article h3 {
      font-size: 1.28rem;
      font-style: italic;
    }

    .note-article p,
    .note-article ul,
    .note-article ol,
    .note-article pre,
    .note-article blockquote,
    .math-display-source {
      margin: 0 0 1.2rem;
    }

    .note-article ul,
    .note-article ol {
      padding-left: 1.3rem;
    }

    .note-article li + li {
      margin-top: 0.35rem;
    }

    .note-article code {
      font-size: 0.9em;
    }

    .note-article pre {
      overflow-x: auto;
      padding: 1rem 0;
      border-top: 1px solid var(--rule);
      border-bottom: 1px solid var(--rule);
      color: var(--muted);
      line-height: 1.5;
    }

    .note-article blockquote {
      padding-left: 1.25rem;
      border-left: 1px solid var(--rule);
      color: var(--muted);
    }

    @media (max-width: 768px) {
      body {
        font-size: 17px;
      }

      .theme-toggle {
        top: 0.75rem;
        right: 0.75rem;
      }

      .page {
        padding: 4.5rem 1.25rem 3rem;
      }

      .topline {
        margin-bottom: 3rem;
      }

      h1 {
        font-size: 3.25rem;
        line-height: 1;
      }

      .lede {
        font-size: 1.15rem;
      }

      section {
        display: block;
        padding: 3rem 0;
      }

      section > h2 {
        margin: 0 0 1.5rem;
      }
    }

    @media (max-width: 420px) {
      h1 {
        font-size: 2.75rem;
      }
    }
"""


THEME_SCRIPT = r"""
    function setThemeControl(isDarkMode) {
      document.getElementById('mode-label').textContent = isDarkMode ? '☼' : '☾';
      document.querySelector('.theme-toggle').setAttribute('aria-label', isDarkMode ? 'Switch to light mode' : 'Switch to dark mode');
    }

    function toggleDarkMode() {
      const body = document.body;
      body.classList.toggle('dark');
      const isDarkMode = body.classList.contains('dark');
      localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
      setThemeControl(isDarkMode);
    }

    window.onload = () => {
      const isDarkMode = localStorage.getItem('theme') === 'dark';
      if (isDarkMode) {
        document.body.classList.add('dark');
      }
      setThemeControl(isDarkMode);

      renderMathInElement(document.body, {
          delimiters: [
              {left: "$$", right: "$$", display: true}, {left: "$", right: "$", display: false}
          ],
          throwOnError: false
      });
    };
"""


EDITOR_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>Notes Editor</title>
<link href="https://fonts.googleapis.com" rel="preconnect"/>
<link crossorigin="" href="https://fonts.gstatic.com" rel="preconnect"/>
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400..700&amp;display=swap" rel="stylesheet"/>
<link href="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.7.1/katex.min.css" rel="stylesheet"/>
<script src="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.7.1/katex.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.7.1/contrib/auto-render.min.js"></script>
<style>
    :root {
      --bg: #f4f7f4;
      --surface: #edf2ee;
      --text: #191b18;
      --muted: #687069;
      --accent: #517783;
      --rule: #d7ded8;
      --danger: #9a3d37;
    }

    *, *::before, *::after {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      min-height: 100vh;
      background: var(--bg);
      color: var(--text);
      font-family: "Source Serif 4", Georgia, "Times New Roman", serif;
      font-size: 17px;
      line-height: 1.6;
      -webkit-font-smoothing: antialiased;
      text-rendering: optimizeLegibility;
    }

    button,
    input,
    textarea {
      font: inherit;
    }

    button {
      border: 0;
      padding: 0;
      background: transparent;
      color: inherit;
      cursor: pointer;
    }

    a {
      color: inherit;
      text-decoration-color: var(--accent);
      text-decoration-thickness: 0.06em;
      text-underline-offset: 0.18em;
    }

    a:hover,
    button:hover {
      color: var(--accent);
    }

    .shell {
      display: grid;
      grid-template-columns: minmax(16rem, 24rem) minmax(0, 1fr);
      min-height: 100vh;
    }

    aside {
      min-height: 100vh;
      padding: 2rem;
      border-right: 1px solid var(--rule);
    }

    .brand {
      margin-bottom: 2.5rem;
    }

    .brand h1 {
      margin: 0;
      font-size: 2.35rem;
      font-weight: 500;
      line-height: 1;
      letter-spacing: 0;
    }

    .brand p {
      max-width: 18rem;
      margin: 0.85rem 0 0;
      color: var(--muted);
      font-size: 1rem;
      line-height: 1.45;
    }

    .sidebar-actions {
      display: flex;
      gap: 1rem;
      margin-bottom: 1.5rem;
      padding-bottom: 1.5rem;
      border-bottom: 1px solid var(--rule);
    }

    .text-button {
      color: var(--text);
      font-weight: 600;
      text-decoration: none;
    }

    .text-button.danger {
      color: var(--danger);
    }

    .text-button[disabled] {
      color: var(--muted);
      cursor: default;
      opacity: 0.55;
    }

    .note-list {
      display: grid;
      gap: 0;
      margin: 0;
      padding: 0;
      list-style: none;
    }

    .note-item {
      width: 100%;
      padding: 1rem 0;
      border-bottom: 1px solid var(--rule);
      text-align: left;
    }

    .note-item.active .note-item-title {
      color: var(--accent);
    }

    .note-item-title {
      display: block;
      font-weight: 600;
      line-height: 1.35;
    }

    .note-item-date {
      display: block;
      margin-top: 0.25rem;
      color: var(--muted);
      font-size: 0.95rem;
    }

    .note-item-status {
      color: var(--accent);
      font-style: italic;
    }

    .empty-list {
      margin: 0;
      color: var(--muted);
    }

    main {
      min-width: 0;
      padding: 2rem 2.5rem 4rem;
    }

    .topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1.5rem;
      margin-bottom: 2.5rem;
      padding-bottom: 1.5rem;
      border-bottom: 1px solid var(--rule);
    }

    .tabs {
      display: flex;
      gap: 1rem;
    }

    .tab {
      color: var(--muted);
      font-weight: 600;
    }

    .tab.active {
      color: var(--text);
      text-decoration: underline;
      text-decoration-color: var(--accent);
      text-underline-offset: 0.2em;
    }

    .status {
      min-height: 1.5rem;
      color: var(--muted);
      font-size: 0.98rem;
      text-align: right;
    }

    .editor-grid {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(12rem, 16rem);
      gap: 2rem;
      align-items: start;
    }

    label {
      display: block;
      margin-bottom: 1.4rem;
    }

    .label-text {
      display: block;
      margin-bottom: 0.35rem;
      color: var(--muted);
      font-size: 0.95rem;
    }

    input,
    textarea {
      width: 100%;
      border: 0;
      border-bottom: 1px solid var(--rule);
      border-radius: 0;
      background: transparent;
      color: var(--text);
      outline: 0;
    }

    input:focus,
    textarea:focus {
      border-color: var(--accent);
    }

    input {
      padding: 0.35rem 0;
    }

    #title {
      font-size: 2rem;
      line-height: 1.15;
    }

    textarea {
      min-height: 52vh;
      padding: 0.75rem 0;
      resize: vertical;
      line-height: 1.55;
    }

    .field-note {
      margin: -0.7rem 0 1.4rem;
      color: var(--muted);
      font-size: 0.92rem;
      line-height: 1.4;
    }

    .visibility-note {
      margin: 0 0 1.4rem;
      color: var(--muted);
      font-size: 0.98rem;
      line-height: 1.45;
    }

    .confirm-panel {
      display: none;
      margin-top: 1rem;
      padding-top: 1rem;
      border-top: 1px solid var(--rule);
    }

    .confirm-panel.active {
      display: block;
    }

    .confirm-panel p {
      margin: 0 0 0.85rem;
      color: var(--muted);
      line-height: 1.45;
    }

    .confirm-title {
      color: var(--text);
      font-weight: 600;
    }

    .side-fields {
      padding-top: 0.4rem;
    }

    .panel {
      display: none;
    }

    .panel.active {
      display: block;
    }

    .preview-shell {
      max-width: 760px;
    }

    .preview-note {
      color: var(--muted);
      margin-bottom: 1.5rem;
      font-size: 0.98rem;
    }

    .note-article h1,
    .guide h1 {
      margin: 0;
      font-size: 3.25rem;
      font-weight: 500;
      line-height: 1;
      letter-spacing: 0;
    }

    .note-date {
      display: block;
      margin-top: 1rem;
      color: var(--muted);
      font-size: 1rem;
    }

    .note-description {
      max-width: 38rem;
      margin: 1.15rem 0 2.75rem;
      color: var(--muted);
      font-size: 1.2rem;
      line-height: 1.45;
    }

    .note-body {
      max-width: 720px;
      padding-top: 2.5rem;
      border-top: 1px solid var(--rule);
    }

    .note-body h2,
    .note-body h3,
    .guide h2,
    .guide h3 {
      margin: 2.4rem 0 0.8rem;
      font-weight: 500;
      line-height: 1.25;
    }

    .note-body h2,
    .guide h2 {
      font-size: 1.6rem;
    }

    .note-body h3,
    .guide h3 {
      font-size: 1.28rem;
      font-style: italic;
    }

    .note-body p,
    .note-body ul,
    .note-body ol,
    .note-body pre,
    .note-body blockquote,
    .math-display-source,
    .guide p,
    .guide ul,
    .guide pre {
      margin: 0 0 1.2rem;
    }

    .note-body ul,
    .note-body ol,
    .guide ul {
      padding-left: 1.3rem;
    }

    .note-body li + li,
    .guide li + li {
      margin-top: 0.35rem;
    }

    .note-body pre,
    .guide pre {
      overflow-x: auto;
      padding: 1rem 0;
      border-top: 1px solid var(--rule);
      border-bottom: 1px solid var(--rule);
      color: var(--muted);
      line-height: 1.5;
    }

    .note-body blockquote,
    .guide blockquote {
      padding-left: 1.25rem;
      border-left: 1px solid var(--rule);
      color: var(--muted);
    }

    .guide {
      max-width: 760px;
    }

    .guide .lede {
      max-width: 38rem;
      margin: 1.15rem 0 3rem;
      color: var(--muted);
      font-size: 1.2rem;
      line-height: 1.45;
    }

    @media (max-width: 900px) {
      .shell {
        display: block;
      }

      aside {
        min-height: auto;
        border-right: 0;
        border-bottom: 1px solid var(--rule);
      }

      main {
        padding: 2rem 1.5rem 3rem;
      }

      .editor-grid {
        display: block;
      }

      .topbar {
        align-items: flex-start;
        flex-direction: column;
      }

      .status {
        text-align: left;
      }
    }
</style>
</head>
<body>
<div class="shell">
<aside>
<div class="brand">
<h1>Notes Editor</h1>
<p>Write locally, review with rendered TeX, then save to the static site.</p>
</div>
<div class="sidebar-actions">
<button class="text-button" id="newBtn" type="button">New</button>
<button class="text-button" id="siteIndexBtn" type="button">Open notes page</button>
<button class="text-button" id="quitBtn" type="button">Quit editor</button>
</div>
<ul class="note-list" id="noteList"></ul>
</aside>
<main>
<div class="topbar">
<div class="tabs" role="tablist" aria-label="Editor modes">
<button class="tab active" data-mode="write" type="button">Write</button>
<button class="tab" data-mode="review" type="button">Review</button>
<button class="tab" data-mode="guide" type="button">Guide</button>
</div>
<div class="status" id="status">Ready.</div>
</div>

<section class="panel active" id="writePanel">
<div class="editor-grid">
<div>
<label>
<span class="label-text">Title</span>
<input autocomplete="off" id="title" placeholder="A note on..." type="text"/>
</label>
<label>
<span class="label-text">Body</span>
<textarea id="body" spellcheck="true" placeholder="Write Markdown and TeX here. Switch to Review to see the latest rendered version."></textarea>
</label>
</div>
<div class="side-fields">
<label>
<span class="label-text">Date</span>
<input id="date" type="date"/>
</label>
<label>
<span class="label-text">Description</span>
<textarea id="description" placeholder="One or two quiet sentences for the notes index."></textarea>
</label>
<p class="field-note" id="slugNote">URL appears after saving.</p>
<p class="visibility-note" id="visibilityNote">New notes publish when saved.</p>
<div class="sidebar-actions">
<button class="text-button" id="saveBtn" type="button">Save</button>
<button class="text-button" id="visibilityBtn" type="button">Hide from site</button>
<button class="text-button" id="openPageBtn" type="button">Open site page</button>
<button class="text-button danger" id="deleteBtn" type="button">Delete</button>
</div>
<div class="confirm-panel" id="deleteConfirm">
<p><span class="confirm-title" id="deleteConfirmTitle">Delete this note?</span><br/>This removes it from the editor and from the generated site.</p>
<div class="sidebar-actions">
<button class="text-button" id="cancelDeleteBtn" type="button">Cancel</button>
<button class="text-button danger" id="confirmDeleteBtn" type="button">Delete permanently</button>
</div>
</div>
</div>
</div>
</section>

<section class="panel" id="reviewPanel">
<div class="preview-shell">
<p class="preview-note">Preview is rendered from the current editor text, including unsaved changes.</p>
<div id="preview"></div>
</div>
</section>

<section class="panel" id="guidePanel">
<div class="guide">
<h1>Markdown and TeX</h1>
<p class="lede">Use plain text for paragraphs, a few Markdown marks for structure, and ordinary LaTeX delimiters for mathematics.</p>

<h2>Headings</h2>
<pre><code># Large heading
## Section heading
### Subsection heading</code></pre>

<h2>Emphasis</h2>
<pre><code>*italic text*
**bold text**
`inline code`</code></pre>

<h2>Lists</h2>
<pre><code>- first point
- second point

1. first step
2. second step</code></pre>

<h2>Links</h2>
<pre><code>[arXiv](https://arxiv.org/)</code></pre>

<h2>Mathematics</h2>
<pre><code>Inline math uses dollar signs: $\Omega(nd)$.

Display math uses double dollar signs:

$$
\sum_{i=1}^n x_i^2
$$</code></pre>

<h2>A Tiny Note</h2>
<pre><code>## Palindrome Polynomial

We consider the $n$-variate degree $d$ palindrome polynomial.

The lower bound is:

$$
\Omega(nd).
$$

The proof has two ingredients:

- a rank measure
- a decomposition argument</code></pre>
</div>
</section>
</main>
</div>

<script>
const state = {
  notes: [],
  currentId: null,
  currentSlug: "",
  currentPublished: true,
  dirty: false,
  mode: "write",
  previewTimer: null
};

const els = {
  noteList: document.getElementById("noteList"),
  title: document.getElementById("title"),
  date: document.getElementById("date"),
  description: document.getElementById("description"),
  body: document.getElementById("body"),
  slugNote: document.getElementById("slugNote"),
  visibilityNote: document.getElementById("visibilityNote"),
  visibilityBtn: document.getElementById("visibilityBtn"),
  openPageBtn: document.getElementById("openPageBtn"),
  deleteBtn: document.getElementById("deleteBtn"),
  deleteConfirm: document.getElementById("deleteConfirm"),
  deleteConfirmTitle: document.getElementById("deleteConfirmTitle"),
  status: document.getElementById("status"),
  preview: document.getElementById("preview")
};

function today() {
  return new Date().toISOString().slice(0, 10);
}

function setStatus(message) {
  els.status.textContent = message;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
  return response.json();
}

function collectNote() {
  return {
    id: state.currentId,
    slug: state.currentSlug,
    published: state.currentPublished,
    title: els.title.value.trim(),
    date: els.date.value,
    description: els.description.value.trim(),
    body: els.body.value
  };
}

function fillNote(note) {
  state.currentId = note.id || null;
  state.currentSlug = note.slug || "";
  state.currentPublished = note.published !== false;
  els.title.value = note.title || "";
  els.date.value = note.date || today();
  els.description.value = note.description || "";
  els.body.value = note.body || "";
  updateLifecycleControls();
  hideDeleteConfirmation();
  state.dirty = false;
  renderList();
  setStatus(state.currentId ? `Loaded ${state.currentPublished ? "published" : "hidden"} note.` : "New note.");
  if (state.mode === "review") {
    renderPreview();
  }
}

function updateLifecycleControls() {
  const saved = Boolean(state.currentId);
  els.slugNote.textContent = state.currentSlug ? `URL: notes/${state.currentSlug}.html` : "URL appears after saving.";
  els.visibilityNote.textContent = saved
    ? (state.currentPublished ? "Published: appears on the public notes page." : "Hidden: editable here, absent from the public site.")
    : "New notes publish when saved.";
  els.visibilityBtn.textContent = state.currentPublished ? "Hide from site" : "Publish to site";
  els.visibilityBtn.disabled = !saved;
  els.openPageBtn.disabled = !saved || !state.currentPublished;
  els.deleteBtn.disabled = !saved;
}

function newNote() {
  fillNote({
    id: null,
    slug: "",
    published: true,
    title: "",
    date: today(),
    description: "",
    body: "## A first section\n\nWrite here. Inline math looks like $x^2$.\n\n$$\n\\Omega(nd)\n$$\n"
  });
  switchMode("write");
  els.title.focus();
}

function renderList() {
  els.noteList.innerHTML = "";
  if (!state.notes.length) {
    const empty = document.createElement("li");
    empty.className = "empty-list";
    empty.textContent = "No saved notes yet.";
    els.noteList.appendChild(empty);
    return;
  }

  for (const note of state.notes) {
    const li = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.className = "note-item" + (note.id === state.currentId ? " active" : "");
    button.innerHTML = `<span class="note-item-title"></span><span class="note-item-date"></span>`;
    button.querySelector(".note-item-title").textContent = note.title || "Untitled note";
    button.querySelector(".note-item-date").innerHTML = `<span></span> · <span class="note-item-status"></span>`;
    button.querySelector(".note-item-date span:first-child").textContent = note.date || "No date";
    button.querySelector(".note-item-status").textContent = note.published === false ? "Hidden" : "Published";
    button.addEventListener("click", () => selectNote(note.id));
    li.appendChild(button);
    els.noteList.appendChild(li);
  }
}

function selectNote(id) {
  const note = state.notes.find(item => item.id === id);
  if (!note) return;
  if (state.dirty && !confirm("Discard unsaved changes and open another note?")) {
    return;
  }
  fillNote(note);
}

async function loadNotes() {
  const data = await api("/api/notes");
  state.notes = data.notes || [];
  renderList();
  const requested = new URLSearchParams(window.location.search).get("note");
  const requestedNote = state.notes.find(note => note.id === requested);
  if (requestedNote) {
    fillNote(requestedNote);
  } else if (state.notes.length) {
    fillNote(state.notes[0]);
  } else {
    newNote();
  }
}

async function saveNote() {
  const note = collectNote();
  if (!note.title) {
    setStatus("Give the note a title first.");
    els.title.focus();
    return;
  }
  setStatus("Saving...");
  const data = await api("/api/save", {
    method: "POST",
    body: JSON.stringify(note)
  });
  state.notes = data.notes || [];
  fillNote(data.note);
  setStatus("Saved and rebuilt.");
}

function showDeleteConfirmation() {
  if (!state.currentId) {
    return;
  }
  els.deleteConfirmTitle.textContent = `Delete “${els.title.value.trim() || "Untitled note"}”?`;
  els.deleteConfirm.classList.add("active");
  setStatus("Confirm deletion.");
}

function hideDeleteConfirmation() {
  els.deleteConfirm.classList.remove("active");
}

async function deleteNote() {
  if (!state.currentId) {
    newNote();
    return;
  }
  setStatus("Deleting...");
  const data = await api("/api/delete", {
    method: "POST",
    body: JSON.stringify({ id: state.currentId })
  });
  state.notes = data.notes || [];
  if (state.notes.length) {
    fillNote(state.notes[0]);
  } else {
    newNote();
  }
  setStatus("Deleted and rebuilt.");
}

async function updateVisibility(published) {
  if (!state.currentId) {
    setStatus("Save the note before changing visibility.");
    return;
  }
  const note = collectNote();
  note.published = published;
  setStatus(published ? "Publishing..." : "Hiding...");
  const data = await api("/api/save", {
    method: "POST",
    body: JSON.stringify(note)
  });
  state.notes = data.notes || [];
  fillNote(data.note);
  setStatus(published ? "Published to site." : "Hidden from site.");
}

async function renderPreview() {
  setStatus(state.dirty ? "Rendering unsaved preview..." : "Rendering preview...");
  const data = await api("/api/render", {
    method: "POST",
    body: JSON.stringify(collectNote())
  });
  els.preview.innerHTML = data.html;
  if (window.renderMathInElement) {
    renderMathInElement(els.preview, {
      delimiters: [
        { left: "$$", right: "$$", display: true },
        { left: "$", right: "$", display: false }
      ],
      throwOnError: false
    });
  }
  setStatus(state.dirty ? "Previewing unsaved changes." : "Preview ready.");
}

function schedulePreview() {
  if (state.mode !== "review") return;
  window.clearTimeout(state.previewTimer);
  state.previewTimer = window.setTimeout(renderPreview, 250);
}

function switchMode(mode) {
  state.mode = mode;
  document.querySelectorAll(".tab").forEach(tab => {
    tab.classList.toggle("active", tab.dataset.mode === mode);
  });
  document.querySelectorAll(".panel").forEach(panel => {
    panel.classList.remove("active");
  });
  document.getElementById(`${mode}Panel`).classList.add("active");
  if (mode === "review") {
    renderPreview();
  } else if (mode === "guide") {
    setStatus("Guide open.");
  } else {
    setStatus(state.dirty ? "Editing unsaved changes." : "Ready.");
  }
}

function openCurrentPage() {
  if (!state.currentSlug || !state.currentPublished) {
    setStatus(state.currentSlug ? "Publish first, then open the site page." : "Save first, then open the site page.");
    return;
  }
  window.open(`/site/notes/${state.currentSlug}.html`, "_blank");
}

function markDirty() {
  state.dirty = true;
  hideDeleteConfirmation();
  setStatus("Unsaved changes.");
  schedulePreview();
}

async function quitEditor() {
  setStatus("Closing editor...");
  try {
    await api("/api/quit", { method: "POST", body: JSON.stringify({}) });
  } finally {
    document.body.innerHTML = '<main style="max-width: 42rem; margin: 0 auto; padding: 6rem 2rem; font-family: Source Serif 4, Georgia, serif;"><h1 style="font-weight: 500; font-size: 3rem; line-height: 1;">Editor closed</h1><p style="color: #687069; font-size: 1.2rem;">The local notes editor has stopped. You can close this tab.</p></main>';
  }
}

document.getElementById("newBtn").addEventListener("click", () => {
  if (state.dirty && !confirm("Discard unsaved changes and start a new note?")) {
    return;
  }
  newNote();
});
document.getElementById("saveBtn").addEventListener("click", () => saveNote().catch(error => setStatus(error.message)));
document.getElementById("visibilityBtn").addEventListener("click", () => updateVisibility(!state.currentPublished).catch(error => setStatus(error.message)));
document.getElementById("deleteBtn").addEventListener("click", showDeleteConfirmation);
document.getElementById("cancelDeleteBtn").addEventListener("click", hideDeleteConfirmation);
document.getElementById("confirmDeleteBtn").addEventListener("click", () => deleteNote().catch(error => setStatus(error.message)));
document.getElementById("openPageBtn").addEventListener("click", openCurrentPage);
document.getElementById("siteIndexBtn").addEventListener("click", () => window.open("/site/notes/index.html", "_blank"));
document.getElementById("quitBtn").addEventListener("click", () => quitEditor().catch(error => setStatus(error.message)));
document.querySelectorAll(".tab").forEach(tab => {
  tab.addEventListener("click", () => switchMode(tab.dataset.mode));
});
[els.title, els.date, els.description, els.body].forEach(input => {
  input.addEventListener("input", markDirty);
});

loadNotes().catch(error => setStatus(error.message));
</script>
</body>
</html>
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def escape(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def load_data() -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        return {"notes": []}
    with DATA_FILE.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        return {"notes": []}
    notes = data.get("notes")
    if not isinstance(notes, list):
        data["notes"] = []
    else:
        for note in notes:
            if isinstance(note, dict) and "published" not in note:
                note["published"] = True
    return data


def write_data(data: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = DATA_FILE.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    tmp.replace(DATA_FILE)


def sorted_notes(notes: list[dict]) -> list[dict]:
    return sorted(
        notes,
        key=lambda note: (note.get("date") or "", note.get("updated") or "", note.get("title") or ""),
        reverse=True,
    )


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", normalized.lower()).strip("-")
    slug = re.sub(r"-+", "-", slug)
    return slug[:80].strip("-") or "note"


def unique_slug(title: str, notes: list[dict], current_id: str | None = None) -> str:
    existing = {note.get("slug") for note in notes if note.get("id") != current_id}
    base = slugify(title)
    slug = base
    counter = 2
    while slug in existing:
        slug = f"{base}-{counter}"
        counter += 1
    return slug


def normalize_note(raw: dict, notes: list[dict]) -> dict:
    note_id = str(raw.get("id") or uuid.uuid4().hex)
    existing = next((note for note in notes if note.get("id") == note_id), None)
    title = str(raw.get("title") or "Untitled note").strip() or "Untitled note"
    note_date = str(raw.get("date") or date.today().isoformat()).strip() or date.today().isoformat()
    description = str(raw.get("description") or "").strip()
    body = str(raw.get("body") or "").replace("\r\n", "\n").replace("\r", "\n")
    slug = existing.get("slug") if existing else unique_slug(title, notes, note_id)
    published = raw.get("published")
    if published is None:
        published = existing.get("published", True) if existing else True

    return {
        "id": note_id,
        "slug": slug,
        "published": published is not False,
        "title": title,
        "date": note_date,
        "description": description,
        "body": body,
        "created": existing.get("created") if existing else now_iso(),
        "updated": now_iso(),
    }


def protect_inline(text: str) -> tuple[str, dict[str, str]]:
    replacements: dict[str, str] = {}

    def put(value: str) -> str:
        token = f"@@NOTE_TOKEN_{len(replacements)}@@"
        replacements[token] = value
        return token

    def code_repl(match: re.Match[str]) -> str:
        return put(f"<code>{escape(match.group(1))}</code>")

    text = re.sub(r"`([^`\n]+)`", code_repl, text)

    def math_repl(match: re.Match[str]) -> str:
        return put(escape(match.group(0)))

    text = re.sub(r"(\$\$.*?\$\$|\$[^$\n]+\$)", math_repl, text)
    return text, replacements


def render_inline(text: str) -> str:
    protected, replacements = protect_inline(text)
    rendered = escape(protected)

    def link_repl(match: re.Match[str]) -> str:
        label = match.group(1)
        href = match.group(2)
        if not href.startswith(("http://", "https://", "mailto:", "../", "./", "#", "/")):
            href = "#"
        return f'<a href="{escape(href)}">{label}</a>'

    rendered = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link_repl, rendered)
    rendered = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", rendered)
    rendered = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", rendered)

    for token, value in replacements.items():
        rendered = rendered.replace(token, value)
    return rendered


def is_block_start(line: str) -> bool:
    stripped = line.strip()
    return bool(
        not stripped
        or stripped == "$$"
        or stripped.startswith("```")
        or re.match(r"#{1,3}\s+", line)
        or re.match(r"\s*[-*]\s+", line)
        or re.match(r"\s*\d+\.\s+", line)
        or line.startswith("> ")
    )


def render_markdown(markdown: str) -> str:
    lines = markdown.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    output: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if stripped.startswith("```"):
            i += 1
            code_lines: list[str] = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1
            output.append(f"<pre><code>{escape(chr(10).join(code_lines))}</code></pre>")
            continue

        if stripped == "$$":
            math_lines = ["$$"]
            i += 1
            while i < len(lines):
                math_lines.append(lines[i])
                if lines[i].strip() == "$$":
                    i += 1
                    break
                i += 1
            output.append(f'<div class="math-display-source">{escape(chr(10).join(math_lines))}</div>')
            continue

        heading = re.match(r"^(#{1,3})\s+(.+)$", line)
        if heading:
            level = len(heading.group(1))
            output.append(f"<h{level}>{render_inline(heading.group(2).strip())}</h{level}>")
            i += 1
            continue

        if re.match(r"\s*[-*]\s+", line):
            items: list[str] = []
            while i < len(lines) and re.match(r"\s*[-*]\s+", lines[i]):
                item = re.sub(r"^\s*[-*]\s+", "", lines[i]).strip()
                items.append(f"<li>{render_inline(item)}</li>")
                i += 1
            output.append(f"<ul>{''.join(items)}</ul>")
            continue

        if re.match(r"\s*\d+\.\s+", line):
            items = []
            while i < len(lines) and re.match(r"\s*\d+\.\s+", lines[i]):
                item = re.sub(r"^\s*\d+\.\s+", "", lines[i]).strip()
                items.append(f"<li>{render_inline(item)}</li>")
                i += 1
            output.append(f"<ol>{''.join(items)}</ol>")
            continue

        if line.startswith("> "):
            quote_lines: list[str] = []
            while i < len(lines) and lines[i].startswith("> "):
                quote_lines.append(lines[i][2:].strip())
                i += 1
            output.append(f"<blockquote>{render_inline(' '.join(quote_lines))}</blockquote>")
            continue

        paragraph: list[str] = []
        while i < len(lines) and not is_block_start(lines[i]):
            paragraph.append(lines[i].strip())
            i += 1
        output.append(f"<p>{render_inline(' '.join(paragraph))}</p>")

    return "\n".join(output) or '<p class="empty-note">No body yet.</p>'


def render_note_article(note: dict) -> str:
    title = escape(note.get("title") or "Untitled note")
    note_date = escape(note.get("date") or "")
    description = escape(note.get("description") or "")
    body = render_markdown(note.get("body") or "")
    description_html = f'<p class="note-description">{description}</p>' if description else ""
    date_html = f'<span class="note-date">{note_date}</span>' if note_date else ""
    return f"""
<article class="note-article">
<h1>{title}</h1>
{date_html}
{description_html}
<div class="note-body">
{body}
</div>
</article>
""".strip()


def wrap_site_page(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
{GENERATED_MARKER}
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>{escape(title)}</title>
<link href="https://fonts.googleapis.com" rel="preconnect"/>
<link crossorigin="" href="https://fonts.gstatic.com" rel="preconnect"/>
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400..700&amp;display=swap" rel="stylesheet"/>
<link href="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.7.1/katex.min.css" rel="stylesheet"/>
<script src="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.7.1/katex.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.7.1/contrib/auto-render.min.js"></script>
<style>
{SITE_CSS}
</style>
</head>
<body>
<button aria-label="Switch to dark mode" class="theme-toggle" onclick="toggleDarkMode()"><span aria-hidden="true" id="mode-label">☾</span></button>
{body}
<script>
{THEME_SCRIPT}
</script>
</body>
</html>
"""


def render_notes_index(notes: list[dict]) -> str:
    published_notes = [note for note in notes if note.get("published", True) is not False]
    if published_notes:
        entries = []
        for note in sorted_notes(published_notes):
            title = escape(note.get("title") or "Untitled note")
            note_date = escape(note.get("date") or "")
            description = escape(note.get("description") or "")
            slug = escape(note.get("slug") or "")
            meta_parts = [part for part in [note_date, description] if part]
            meta = " · ".join(meta_parts)
            meta_html = f'<span class="note-meta">{meta}</span>' if meta else ""
            entries.append(
                f"""<li>
<a class="note-title" href="{slug}.html">{title}</a>
{meta_html}
</li>"""
            )
        list_html = "\n".join(entries)
    else:
        list_html = '<li><p class="empty-note">No notes yet.</p></li>'

    body = f"""
<div class="page">
<nav aria-label="Site links" class="topline">
<a href="../index.html">Home</a>
</nav>
<header>
<h1>Notes</h1>
<p class="lede">{escape(DEFAULT_LEDE)}</p>
</header>
<main>
<section>
<h2>Index</h2>
<ul class="note-list">
{list_html}
</ul>
</section>
</main>
</div>
""".strip()
    return wrap_site_page("Notes | Pratik Shastri", body)


def render_single_note(note: dict) -> str:
    body = f"""
<div class="page">
<nav aria-label="Site links" class="topline">
<a href="../index.html">Home</a>
<a href="index.html">Notes</a>
</nav>
<main>
<section>
<h2>Note</h2>
{render_note_article(note)}
</section>
</main>
</div>
""".strip()
    return wrap_site_page(f"{note.get('title') or 'Untitled note'} | Pratik Shastri", body)


def remove_stale_note_pages(valid_slugs: set[str]) -> None:
    if not NOTES_DIR.exists():
        return
    for path in NOTES_DIR.glob("*.html"):
        if path.name == "index.html":
            continue
        if path.stem in valid_slugs:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if GENERATED_MARKER in text:
            path.unlink()


def render_site() -> None:
    data = load_data()
    notes = data.get("notes", [])
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    published_notes = [note for note in notes if note.get("published", True) is not False]
    valid_slugs = {note.get("slug") for note in published_notes if note.get("slug")}
    remove_stale_note_pages(set(valid_slugs))
    (NOTES_DIR / "index.html").write_text(render_notes_index(notes), encoding="utf-8")
    for note in published_notes:
        slug = note.get("slug")
        if not slug:
            continue
        (NOTES_DIR / f"{slug}.html").write_text(render_single_note(note), encoding="utf-8")


class NotesHandler(BaseHTTPRequestHandler):
    server_version = "NotesEditor/1.0"

    def log_message(self, fmt: str, *args: object) -> None:
        sys.stdout.write("%s - %s\n" % (self.address_string(), fmt % args))

    def send_text(self, status: int, text: str, content_type: str = "text/plain; charset=utf-8") -> None:
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length") or "0")
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            self.send_text(200, EDITOR_HTML, "text/html; charset=utf-8")
            return
        if path == "/api/notes":
            data = load_data()
            self.send_json({"notes": sorted_notes(data.get("notes", []))})
            return
        if path == "/api/health":
            self.send_json({"ok": True})
            return
        if path.startswith("/site/"):
            self.serve_site_file(path.removeprefix("/site/"))
            return
        self.send_text(404, "Not found")

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            payload = self.read_json()
            if path == "/api/render":
                note = normalize_note(payload, [])
                note["slug"] = payload.get("slug") or ""
                self.send_json({"html": render_note_article(note)})
                return
            if path == "/api/save":
                data = load_data()
                notes = data.get("notes", [])
                note = normalize_note(payload, notes)
                notes = [item for item in notes if item.get("id") != note["id"]]
                notes.append(note)
                data["notes"] = sorted_notes(notes)
                write_data(data)
                render_site()
                self.send_json({"note": note, "notes": sorted_notes(data["notes"])})
                return
            if path == "/api/delete":
                note_id = str(payload.get("id") or "")
                data = load_data()
                data["notes"] = [note for note in data.get("notes", []) if note.get("id") != note_id]
                write_data(data)
                render_site()
                self.send_json({"notes": sorted_notes(data["notes"])})
                return
            if path == "/api/quit":
                self.send_json({"ok": True})
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                return
        except Exception as exc:  # noqa: BLE001
            self.send_json({"error": str(exc)}, status=500)
            return
        self.send_text(404, "Not found")

    def serve_site_file(self, relative_url_path: str) -> None:
        relative_path = Path(unquote(relative_url_path.lstrip("/")))
        target = (ROOT / relative_path).resolve()
        try:
            target.relative_to(ROOT)
        except ValueError:
            self.send_text(403, "Forbidden")
            return
        if target.is_dir():
            target = target / "index.html"
        if not target.exists() or not target.is_file():
            self.send_text(404, "Not found")
            return
        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def make_server(preferred_port: int) -> ThreadingHTTPServer:
    for port in range(preferred_port, preferred_port + 50):
        try:
            return ThreadingHTTPServer(("127.0.0.1", port), NotesHandler)
        except OSError:
            continue
    raise RuntimeError("Could not find an open local port for the notes editor.")


def run_server(port: int, open_browser: bool = True) -> None:
    render_site()
    server = make_server(port)
    actual_port = server.server_address[1]
    url = f"http://127.0.0.1:{actual_port}/"
    print(f"Notes editor running at {url}")
    print("Use Quit editor in the browser when you are done.")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping notes editor.")
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Local notes editor for the static site.")
    parser.add_argument("--build", action="store_true", help="Regenerate notes pages and exit.")
    parser.add_argument("--no-open", action="store_true", help="Start the server without opening a browser.")
    parser.add_argument("--port", type=int, default=int(os.environ.get("NOTES_EDITOR_PORT", "8765")))
    args = parser.parse_args()

    if args.build:
        render_site()
        print("Notes site rebuilt.")
        return

    run_server(args.port, open_browser=not args.no_open)


if __name__ == "__main__":
    main()
