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
PORT_FILE = DATA_DIR / "editor.port"
NOTES_DIR = ROOT / "notes"
GENERATED_MARKER = "<!-- generated-by-notes-editor -->"
DEFAULT_LEDE = ""
PUBLIC_ROOT_FILES = {
    "index.html",
    "CV.pdf",
    "788f16b6-cb0b-4319-9256-96ad4916cb15.JPG",
}


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

    .citation {
      color: var(--accent);
      font-size: 0.9em;
      text-decoration: none;
      white-space: nowrap;
    }

    .citation a {
      color: inherit;
      text-decoration: none;
    }

    .citation a:hover {
      text-decoration: underline;
      text-decoration-color: var(--accent);
    }

    .citation-missing {
      color: #9a3d37;
      font-size: 0.9em;
      white-space: nowrap;
    }

    .references-section {
      display: block;
      margin-top: 3.25rem;
      padding-top: 1.6rem;
      border-top: 1px solid var(--rule);
    }

    .references-section h2 {
      margin: 0 0 1rem;
      color: var(--muted);
      font-size: 1.05rem;
      font-style: italic;
    }

    .references-list {
      margin: 0;
      padding-left: 1.3rem;
    }

    .references-list li {
      padding-left: 0.25rem;
      margin-bottom: 0.85rem;
    }

    .reference-title {
      font-style: italic;
    }

    .reference-link {
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
      grid-template-columns: minmax(0, 1fr) minmax(14rem, 18rem);
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

    .body-field {
      position: relative;
      margin-bottom: 1.4rem;
    }

    .body-field label {
      margin-bottom: 0;
    }

    .citation-suggest {
      position: absolute;
      left: 0;
      right: auto;
      top: 4.5rem;
      z-index: 20;
      display: none;
      width: min(34rem, 100%);
      max-height: 15rem;
      overflow-y: auto;
      padding: 0.2rem 0;
      border-top: 1px solid var(--accent);
      border-bottom: 1px solid var(--rule);
      background: rgba(244, 247, 244, 0.98);
      box-shadow: 0 1.6rem 2.6rem rgba(25, 27, 24, 0.12);
    }

    .citation-suggest.active {
      display: block;
    }

    .citation-option {
      display: grid;
      gap: 0.15rem;
      width: 100%;
      padding: 0.7rem 0.2rem;
      border-bottom: 1px solid var(--rule);
      text-align: left;
    }

    .citation-option:last-child {
      border-bottom: 0;
    }

    .citation-option.active,
    .citation-option:hover {
      color: var(--text);
      background: rgba(81, 119, 131, 0.08);
    }

    .citation-option-key {
      color: var(--accent);
      font-weight: 600;
      line-height: 1.25;
    }

    .citation-option-meta {
      color: var(--muted);
      font-size: 0.94rem;
      line-height: 1.35;
    }

    .citation-empty {
      margin: 0;
      padding: 0.8rem 0.2rem;
      color: var(--muted);
      font-size: 0.96rem;
      font-style: italic;
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

    .references-editor {
      margin-top: 1.8rem;
      padding-top: 1.2rem;
      border-top: 1px solid var(--rule);
    }

    .references-editor h2 {
      margin: 0;
      font-size: 1.15rem;
      font-weight: 500;
      line-height: 1.25;
    }

    .reference-head {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 1rem;
      margin-bottom: 0.85rem;
    }

    .reference-tools,
    .reference-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 0.8rem;
    }

    .bibtex-import {
      margin: 0.8rem 0 1.2rem;
      padding: 0.85rem 0;
      border-top: 1px solid var(--rule);
      border-bottom: 1px solid var(--rule);
    }

    .bibtex-import[hidden] {
      display: none;
    }

    #bibtexInput {
      min-height: 10rem;
      font-size: 0.98rem;
    }

    .reference-status,
    .reference-warnings {
      margin: 0.75rem 0 0;
      color: var(--muted);
      font-size: 0.94rem;
      line-height: 1.4;
    }

    .reference-warnings {
      margin-bottom: 0.8rem;
      color: var(--danger);
    }

    .reference-list-editor {
      display: grid;
      gap: 1.25rem;
      margin: 0;
      padding: 0;
      list-style: none;
    }

    .reference-item-editor {
      padding-top: 1rem;
      border-top: 1px solid var(--rule);
    }

    .reference-fields {
      display: grid;
      grid-template-columns: minmax(8rem, 0.7fr) minmax(0, 1.3fr);
      gap: 0.7rem 1rem;
    }

    .reference-fields label {
      margin-bottom: 0.35rem;
    }

    .reference-fields textarea {
      min-height: 4.7rem;
      font-size: 0.98rem;
    }

    .reference-summary {
      margin: 0.35rem 0 0.75rem;
      color: var(--muted);
      font-size: 0.94rem;
      line-height: 1.4;
    }

    .empty-references {
      margin: 0;
      color: var(--muted);
      font-size: 0.98rem;
      font-style: italic;
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

    .citation {
      color: var(--accent);
      font-size: 0.9em;
      text-decoration: none;
      white-space: nowrap;
    }

    .citation a {
      color: inherit;
      text-decoration: none;
    }

    .citation a:hover {
      text-decoration: underline;
      text-decoration-color: var(--accent);
    }

    .citation-missing {
      color: var(--danger);
      font-size: 0.9em;
      white-space: nowrap;
    }

    .references-section {
      display: block;
      margin-top: 3rem;
      padding-top: 1.5rem;
      border-top: 1px solid var(--rule);
    }

    .references-section h2 {
      margin: 0 0 1rem;
      color: var(--muted);
      font-size: 1.05rem;
      font-style: italic;
    }

    .references-list {
      margin: 0;
      padding-left: 1.3rem;
    }

    .references-list li {
      padding-left: 0.25rem;
      margin-bottom: 0.85rem;
    }

    .reference-title {
      font-style: italic;
    }

    .reference-link {
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

      .reference-fields {
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
<div class="body-field">
<label for="body">
<span class="label-text">Body</span>
</label>
<textarea id="body" spellcheck="true" placeholder="Write Markdown and TeX here. Switch to Review to see the latest rendered version."></textarea>
<div aria-label="Citation suggestions" class="citation-suggest" id="citationSuggest" role="listbox"></div>
</div>
<section class="references-editor" aria-labelledby="referencesHeading">
<div class="reference-head">
<h2 id="referencesHeading">References</h2>
<div class="reference-tools">
<button class="text-button" id="toggleBibtexBtn" type="button">Paste BibTeX</button>
<button class="text-button" id="addReferenceBtn" type="button">Add manually</button>
</div>
</div>
<div class="bibtex-import" id="bibtexPanel" hidden>
<label>
<span class="label-text">BibTeX</span>
<textarea id="bibtexInput" spellcheck="false" placeholder="@article{nisan1991,&#10;  author = {Nisan, Noam},&#10;  title = {Lower bounds for non-commutative computation},&#10;  year = {1991}&#10;}"></textarea>
</label>
<div class="reference-actions">
<button class="text-button" id="importBibtexBtn" type="button">Add from BibTeX</button>
<button class="text-button" id="clearBibtexBtn" type="button">Clear</button>
</div>
<p class="reference-status" id="bibtexStatus">Paste one entry or many. I will keep the keys and fill the reference list.</p>
</div>
<p class="reference-warnings" id="referenceWarnings"></p>
<ul class="reference-list-editor" id="referenceListEditor"></ul>
</section>
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

<h2>Citations</h2>
<pre><code>Type [@ and choose a saved reference from the dropdown.

Basic citation:
[@nisan1991]

With a locator:
[@nisan1991, Theorem 2.1]

Several references:
[@nisan1991; @raz2013]</code></pre>
<p>Use Paste BibTeX in the References section to add one entry or many entries at once. The dropdown filters by citation-key prefix as you type.</p>

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
  references: [],
  dirty: false,
  mode: "write",
  previewTimer: null,
  refCounter: 0,
  citation: {
    open: false,
    start: 0,
    prefix: "",
    selected: 0,
    suggestions: []
  }
};

const els = {
  noteList: document.getElementById("noteList"),
  title: document.getElementById("title"),
  date: document.getElementById("date"),
  description: document.getElementById("description"),
  body: document.getElementById("body"),
  citationSuggest: document.getElementById("citationSuggest"),
  toggleBibtexBtn: document.getElementById("toggleBibtexBtn"),
  bibtexPanel: document.getElementById("bibtexPanel"),
  bibtexInput: document.getElementById("bibtexInput"),
  bibtexStatus: document.getElementById("bibtexStatus"),
  importBibtexBtn: document.getElementById("importBibtexBtn"),
  clearBibtexBtn: document.getElementById("clearBibtexBtn"),
  addReferenceBtn: document.getElementById("addReferenceBtn"),
  referenceWarnings: document.getElementById("referenceWarnings"),
  referenceListEditor: document.getElementById("referenceListEditor"),
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

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function normalizeReferenceKey(value) {
  return String(value || "")
    .trim()
    .replace(/^@+/, "")
    .replace(/[^A-Za-z0-9:_.-]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function nextReferenceId() {
  state.refCounter += 1;
  return `ref-${Date.now()}-${state.refCounter}`;
}

function normalizeReferenceForEditor(reference = {}) {
  return {
    localId: reference.localId || nextReferenceId(),
    key: normalizeReferenceKey(reference.key),
    author: String(reference.author || "").trim(),
    title: String(reference.title || "").trim(),
    year: String(reference.year || "").trim(),
    venue: String(reference.venue || "").trim(),
    doi: String(reference.doi || "").trim(),
    url: String(reference.url || "").trim(),
    rawBibtex: String(reference.rawBibtex || "").trim()
  };
}

function referenceKeyBase(reference) {
  const authorPart = (reference.author || "ref").split(/,|;|\band\b/i)[0].trim().split(/\s+/).pop() || "ref";
  const yearPart = (reference.year || "").match(/\d{4}/);
  return normalizeReferenceKey(`${authorPart}${yearPart ? yearPart[0] : ""}`.toLowerCase()) || "ref";
}

function uniqueReferenceKey(baseKey, reserved = new Set()) {
  const base = normalizeReferenceKey(baseKey) || "ref";
  let candidate = base;
  let counter = 2;
  while (reserved.has(candidate.toLowerCase())) {
    candidate = `${base}${counter}`;
    counter += 1;
  }
  reserved.add(candidate.toLowerCase());
  return candidate;
}

function collectReferences() {
  const reserved = new Set();
  return state.references
    .map(reference => {
      const clean = normalizeReferenceForEditor(reference);
      const hasContent = ["author", "title", "year", "venue", "doi", "url", "rawBibtex"].some(field => clean[field]);
      if (!clean.key && hasContent) {
        clean.key = uniqueReferenceKey(referenceKeyBase(clean), reserved);
      } else if (clean.key) {
        clean.key = uniqueReferenceKey(clean.key, reserved);
      }
      reference.key = clean.key;
      return clean;
    })
    .filter(reference => reference.key || reference.author || reference.title || reference.year || reference.venue || reference.doi || reference.url)
    .map(({ localId, ...reference }) => reference);
}

function referenceSubtitle(reference) {
  return [reference.author, reference.title, reference.year].filter(Boolean).join(", ") || "Blank reference";
}

function citationKeysInBody() {
  const keys = [];
  const seen = new Set();
  const pattern = /(?:\[@|;\s*@)([A-Za-z0-9:_.-]+)/g;
  let match;
  while ((match = pattern.exec(els.body.value)) !== null) {
    const key = match[1];
    if (!seen.has(key)) {
      seen.add(key);
      keys.push(key);
    }
  }
  return keys;
}

function updateReferenceWarnings() {
  const references = collectReferences();
  const referenceKeys = references.map(reference => reference.key).filter(Boolean);
  const keySet = new Set(referenceKeys);
  const cited = citationKeysInBody();
  const missing = cited.filter(key => !keySet.has(key));
  const unused = referenceKeys.filter(key => !cited.includes(key));
  const messages = [];
  if (missing.length) {
    messages.push(`Missing reference: ${missing.map(key => `@${key}`).join(", ")}.`);
  }
  if (unused.length) {
    messages.push(`Unused: ${unused.map(key => `@${key}`).join(", ")}.`);
  }
  els.referenceWarnings.textContent = messages.join(" ");
}

function renderReferences() {
  els.referenceListEditor.innerHTML = "";
  if (!state.references.length) {
    const empty = document.createElement("li");
    empty.className = "empty-references";
    empty.textContent = "No references yet. Paste BibTeX or add one manually.";
    els.referenceListEditor.appendChild(empty);
    updateReferenceWarnings();
    refreshCitationSuggestions();
    return;
  }

  for (const reference of state.references) {
    const item = document.createElement("li");
    item.className = "reference-item-editor";
    item.dataset.refId = reference.localId;
    item.innerHTML = `
<p class="reference-summary">${escapeHtml(reference.key ? `@${reference.key}` : "No key yet")} · ${escapeHtml(referenceSubtitle(reference))}</p>
<div class="reference-fields">
<label><span class="label-text">Key</span><input autocomplete="off" data-ref-field="key" value="${escapeHtml(reference.key)}" placeholder="nisan1991"/></label>
<label><span class="label-text">Author</span><input autocomplete="off" data-ref-field="author" value="${escapeHtml(reference.author)}" placeholder="Noam Nisan"/></label>
<label><span class="label-text">Year</span><input autocomplete="off" data-ref-field="year" value="${escapeHtml(reference.year)}" placeholder="1991"/></label>
<label><span class="label-text">Venue</span><input autocomplete="off" data-ref-field="venue" value="${escapeHtml(reference.venue)}" placeholder="STOC, journal, preprint"/></label>
<label><span class="label-text">Title</span><textarea data-ref-field="title" placeholder="Paper title">${escapeHtml(reference.title)}</textarea></label>
<label><span class="label-text">DOI or URL</span><textarea data-ref-field="url" placeholder="https://...">${escapeHtml(reference.url || reference.doi)}</textarea></label>
</div>
<div class="reference-actions">
<button class="text-button" data-ref-action="insert" type="button">Insert citation</button>
<button class="text-button danger" data-ref-action="remove" type="button">Remove</button>
</div>`;
    item.querySelectorAll("[data-ref-field]").forEach(input => {
      input.addEventListener("input", () => {
        const field = input.dataset.refField;
        if (field === "url") {
          const value = input.value.trim();
          reference.url = value.startsWith("10.") ? "" : value;
          reference.doi = value.startsWith("10.") ? value : "";
        } else if (field === "key") {
          reference.key = normalizeReferenceKey(input.value);
        } else {
          reference[field] = input.value;
        }
        updateReferenceWarnings();
        refreshCitationSuggestions();
        markDirty();
      });
      input.addEventListener("blur", () => {
        if (input.dataset.refField === "key") {
          input.value = normalizeReferenceKey(input.value);
          reference.key = input.value;
          updateReferenceWarnings();
          refreshCitationSuggestions();
        }
      });
    });
    item.querySelector('[data-ref-action="insert"]').addEventListener("click", () => insertReferenceCitation(reference));
    item.querySelector('[data-ref-action="remove"]').addEventListener("click", () => {
      state.references = state.references.filter(item => item.localId !== reference.localId);
      renderReferences();
      markDirty();
    });
    els.referenceListEditor.appendChild(item);
  }
  updateReferenceWarnings();
  refreshCitationSuggestions();
}

function addBlankReference() {
  state.references.push(normalizeReferenceForEditor({}));
  renderReferences();
  markDirty();
  const inputs = els.referenceListEditor.querySelectorAll('[data-ref-field="key"]');
  if (inputs.length) {
    inputs[inputs.length - 1].focus();
  }
}

function insertTextAtBody(text, putCursorBeforeLastChar = false) {
  const start = els.body.selectionStart;
  const end = els.body.selectionEnd;
  const before = els.body.value.slice(0, start);
  const after = els.body.value.slice(end);
  els.body.value = before + text + after;
  const cursor = before.length + text.length - (putCursorBeforeLastChar ? 1 : 0);
  els.body.focus();
  els.body.setSelectionRange(cursor, cursor);
  markDirty();
}

function insertReferenceCitation(reference) {
  const key = normalizeReferenceKey(reference.key);
  if (!key) {
    setStatus("Give the reference a key first.");
    return;
  }
  insertTextAtBody(`[@${key}]`);
  setStatus(`Inserted @${key}.`);
}

function parseBibtex(text) {
  const entries = [];
  let index = 0;
  while (index < text.length) {
    const at = text.indexOf("@", index);
    if (at === -1) break;
    const typeMatch = text.slice(at + 1).match(/^\s*([A-Za-z]+)\s*([{(])/);
    if (!typeMatch) {
      index = at + 1;
      continue;
    }
    const type = typeMatch[1].toLowerCase();
    const openerIndex = at + 1 + typeMatch[0].lastIndexOf(typeMatch[2]);
    const closerIndex = findBibtexClose(text, openerIndex, typeMatch[2]);
    if (closerIndex === -1) {
      break;
    }
    if (["comment", "preamble", "string"].includes(type)) {
      index = closerIndex + 1;
      continue;
    }
    const content = text.slice(openerIndex + 1, closerIndex);
    const comma = findTopLevelComma(content);
    if (comma !== -1) {
      entries.push({
        type,
        key: content.slice(0, comma).trim(),
        fields: parseBibtexFields(content.slice(comma + 1)),
        rawBibtex: text.slice(at, closerIndex + 1).trim()
      });
    }
    index = closerIndex + 1;
  }
  return entries;
}

function findBibtexClose(text, openerIndex, opener) {
  const closer = opener === "{" ? "}" : ")";
  let depth = 0;
  let inQuote = false;
  let escaped = false;
  for (let i = openerIndex; i < text.length; i += 1) {
    const char = text[i];
    if (escaped) {
      escaped = false;
      continue;
    }
    if (char === "\\") {
      escaped = true;
      continue;
    }
    if (char === '"') {
      inQuote = !inQuote;
      continue;
    }
    if (inQuote) continue;
    if (char === opener) depth += 1;
    if (char === closer) {
      depth -= 1;
      if (depth === 0) return i;
    }
  }
  return -1;
}

function findTopLevelComma(text) {
  let depth = 0;
  let inQuote = false;
  let escaped = false;
  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    if (escaped) {
      escaped = false;
      continue;
    }
    if (char === "\\") {
      escaped = true;
      continue;
    }
    if (char === '"') {
      inQuote = !inQuote;
      continue;
    }
    if (inQuote) continue;
    if (char === "{" || char === "(") depth += 1;
    if (char === "}" || char === ")") depth -= 1;
    if (char === "," && depth === 0) return i;
  }
  return -1;
}

function parseBibtexFields(text) {
  const fields = {};
  let index = 0;
  while (index < text.length) {
    while (index < text.length && /[\s,]/.test(text[index])) index += 1;
    const nameMatch = text.slice(index).match(/^([A-Za-z][A-Za-z0-9_-]*)\s*=/);
    if (!nameMatch) break;
    const name = nameMatch[1].toLowerCase();
    index += nameMatch[0].length;
    const parsed = readBibtexValue(text, index);
    fields[name] = cleanBibtexValue(parsed.value);
    index = parsed.next;
  }
  return fields;
}

function readBibtexValue(text, index) {
  while (index < text.length && /\s/.test(text[index])) index += 1;
  if (text[index] === "{" || text[index] === "(") {
    const close = findBibtexClose(text, index, text[index]);
    return {
      value: close === -1 ? text.slice(index + 1) : text.slice(index + 1, close),
      next: close === -1 ? text.length : close + 1
    };
  }
  if (text[index] === '"') {
    let i = index + 1;
    let escaped = false;
    while (i < text.length) {
      if (escaped) {
        escaped = false;
      } else if (text[i] === "\\") {
        escaped = true;
      } else if (text[i] === '"') {
        break;
      }
      i += 1;
    }
    return { value: text.slice(index + 1, i), next: Math.min(i + 1, text.length) };
  }
  let i = index;
  while (i < text.length && text[i] !== ",") i += 1;
  return { value: text.slice(index, i), next: i };
}

function cleanBibtexValue(value) {
  return String(value || "")
    .replace(/[{}]/g, "")
    .replace(/\\&/g, "&")
    .replace(/\\_/g, "_")
    .replace(/\\-/g, "-")
    .replace(/\s+/g, " ")
    .trim();
}

function bibtexField(fields, names) {
  for (const name of names) {
    if (fields[name]) return fields[name];
  }
  return "";
}

function formatBibtexAuthors(value) {
  return String(value || "")
    .split(/\s+and\s+/i)
    .map(author => {
      const parts = author.split(",").map(part => part.trim()).filter(Boolean);
      return parts.length >= 2 ? `${parts.slice(1).join(" ")} ${parts[0]}` : author.trim();
    })
    .filter(Boolean)
    .join(", ");
}

function importBibtexEntries() {
  const entries = parseBibtex(els.bibtexInput.value);
  if (!entries.length) {
    els.bibtexStatus.textContent = "I could not find a BibTeX entry. Paste an entry beginning with @article, @inproceedings, or similar.";
    return;
  }
  const reserved = new Set(state.references.map(reference => normalizeReferenceKey(reference.key).toLowerCase()).filter(Boolean));
  const imported = entries.map(entry => {
    const fields = entry.fields;
    const doi = bibtexField(fields, ["doi"]);
    const url = bibtexField(fields, ["url", "eprint"]);
    return normalizeReferenceForEditor({
      key: uniqueReferenceKey(entry.key, reserved),
      author: formatBibtexAuthors(bibtexField(fields, ["author", "editor"])),
      title: bibtexField(fields, ["title"]),
      year: bibtexField(fields, ["year", "date"]),
      venue: bibtexField(fields, ["journal", "booktitle", "publisher", "school", "institution", "archiveprefix"]),
      doi,
      url,
      rawBibtex: entry.rawBibtex
    });
  });
  state.references.push(...imported);
  renderReferences();
  markDirty();
  els.bibtexInput.value = "";
  els.bibtexStatus.textContent = `Added ${imported.length} reference${imported.length === 1 ? "" : "s"}.`;
}

function textareaCaretPosition(textarea) {
  const style = window.getComputedStyle(textarea);
  const mirror = document.createElement("div");
  const properties = [
    "boxSizing", "width", "fontFamily", "fontSize", "fontWeight", "fontStyle",
    "letterSpacing", "textTransform", "wordSpacing", "lineHeight", "textAlign",
    "paddingTop", "paddingRight", "paddingBottom", "paddingLeft",
    "borderTopWidth", "borderRightWidth", "borderBottomWidth", "borderLeftWidth"
  ];
  mirror.style.position = "absolute";
  mirror.style.visibility = "hidden";
  mirror.style.whiteSpace = "pre-wrap";
  mirror.style.overflowWrap = "break-word";
  mirror.style.top = "0";
  mirror.style.left = "-9999px";
  mirror.style.width = `${textarea.clientWidth}px`;
  properties.forEach(property => {
    mirror.style[property] = style[property];
  });
  mirror.textContent = textarea.value.slice(0, textarea.selectionStart);
  const marker = document.createElement("span");
  marker.textContent = "\u200b";
  mirror.appendChild(marker);
  document.body.appendChild(mirror);
  const markerRect = marker.getBoundingClientRect();
  const mirrorRect = mirror.getBoundingClientRect();
  document.body.removeChild(mirror);
  const lineHeight = Number.parseFloat(style.lineHeight) || Number.parseFloat(style.fontSize) * 1.4;
  return {
    left: markerRect.left - mirrorRect.left - textarea.scrollLeft,
    top: markerRect.top - mirrorRect.top - textarea.scrollTop + lineHeight
  };
}

function positionCitationSuggestions() {
  if (!state.citation.open) return;
  const field = els.body.closest(".body-field");
  const fieldRect = field.getBoundingClientRect();
  const textareaRect = els.body.getBoundingClientRect();
  const caret = textareaCaretPosition(els.body);
  const minWidth = Math.min(320, fieldRect.width);
  const maxLeft = Math.max(0, fieldRect.width - minWidth);
  const left = Math.min(Math.max(0, textareaRect.left - fieldRect.left + caret.left - 12), maxLeft);
  const top = Math.min(
    textareaRect.top - fieldRect.top + caret.top + 6,
    textareaRect.top - fieldRect.top + els.body.clientHeight - 8
  );
  els.citationSuggest.style.left = `${left}px`;
  els.citationSuggest.style.top = `${Math.max(3.8 * Number.parseFloat(getComputedStyle(document.body).fontSize), top)}px`;
  els.citationSuggest.style.width = `min(34rem, ${Math.max(minWidth, fieldRect.width - left)}px)`;
}

function currentCitationTrigger() {
  if (els.body.selectionStart !== els.body.selectionEnd) return null;
  const cursor = els.body.selectionStart;
  const before = els.body.value.slice(0, cursor);
  const match = before.match(/(?:\[@|;\s*@)([A-Za-z0-9:_.-]*)$/);
  if (!match) return null;
  return {
    prefix: match[1] || "",
    start: cursor - (match[1] || "").length
  };
}

function citationSuggestions(prefix) {
  const lowerPrefix = prefix.toLowerCase();
  return collectReferences()
    .filter(reference => reference.key && reference.key.toLowerCase().startsWith(lowerPrefix))
    .slice(0, 8);
}

function refreshCitationSuggestions() {
  if (!state.citation.open) return;
  const trigger = currentCitationTrigger();
  if (!trigger) {
    closeCitationSuggestions();
    return;
  }
  openCitationSuggestions(trigger);
}

function openCitationSuggestions(trigger) {
  state.citation.open = true;
  state.citation.start = trigger.start;
  state.citation.prefix = trigger.prefix;
  state.citation.suggestions = citationSuggestions(trigger.prefix);
  state.citation.selected = Math.min(state.citation.selected, Math.max(state.citation.suggestions.length - 1, 0));
  renderCitationSuggestions();
}

function renderCitationSuggestions() {
  els.citationSuggest.innerHTML = "";
  els.citationSuggest.classList.add("active");
  if (!state.citation.suggestions.length) {
    const empty = document.createElement("p");
    empty.className = "citation-empty";
    empty.textContent = state.references.length ? "No matching references." : "No references yet.";
    els.citationSuggest.appendChild(empty);
    positionCitationSuggestions();
    return;
  }
  state.citation.suggestions.forEach((reference, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "citation-option" + (index === state.citation.selected ? " active" : "");
    button.setAttribute("role", "option");
    button.setAttribute("aria-selected", index === state.citation.selected ? "true" : "false");
    button.innerHTML = `<span class="citation-option-key">@${escapeHtml(reference.key)}</span><span class="citation-option-meta">${escapeHtml(referenceSubtitle(reference))}</span>`;
    button.addEventListener("mousedown", event => {
      event.preventDefault();
      insertCitationSuggestion(reference);
    });
    els.citationSuggest.appendChild(button);
  });
  positionCitationSuggestions();
}

function closeCitationSuggestions() {
  state.citation.open = false;
  state.citation.suggestions = [];
  els.citationSuggest.classList.remove("active");
  els.citationSuggest.innerHTML = "";
}

function insertCitationSuggestion(reference) {
  const key = normalizeReferenceKey(reference.key);
  if (!key) return;
  const cursor = els.body.selectionStart;
  const before = els.body.value.slice(0, state.citation.start);
  const after = els.body.value.slice(cursor);
  const close = after.startsWith("]") ? "" : "]";
  els.body.value = before + key + close + after;
  const nextCursor = before.length + key.length;
  els.body.focus();
  els.body.setSelectionRange(nextCursor, nextCursor);
  closeCitationSuggestions();
  markDirty();
  setStatus(`Inserted @${key}.`);
}

function collectNote() {
  return {
    id: state.currentId,
    slug: state.currentSlug,
    published: state.currentPublished,
    title: els.title.value.trim(),
    date: els.date.value,
    description: els.description.value.trim(),
    body: els.body.value,
    references: collectReferences()
  };
}

function fillNote(note) {
  state.currentId = note.id || null;
  state.currentSlug = note.slug || "";
  state.currentPublished = note.published !== false;
  state.references = (note.references || []).map(reference => normalizeReferenceForEditor(reference));
  els.title.value = note.title || "";
  els.date.value = note.date || today();
  els.description.value = note.description || "";
  els.body.value = note.body || "";
  updateLifecycleControls();
  renderReferences();
  closeCitationSuggestions();
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
    references: [],
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
  if (state.dirty) {
    setStatus("Save or discard unsaved edits before changing visibility.");
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
  updateReferenceWarnings();
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
[els.title, els.date, els.description].forEach(input => {
  input.addEventListener("input", markDirty);
});
els.body.addEventListener("input", () => {
  markDirty();
  const trigger = currentCitationTrigger();
  if (trigger) {
    openCitationSuggestions(trigger);
  } else {
    closeCitationSuggestions();
  }
});
els.body.addEventListener("keydown", event => {
  if (!state.citation.open) return;
  if (event.key === "ArrowDown") {
    event.preventDefault();
    state.citation.selected = Math.min(state.citation.selected + 1, state.citation.suggestions.length - 1);
    renderCitationSuggestions();
  } else if (event.key === "ArrowUp") {
    event.preventDefault();
    state.citation.selected = Math.max(state.citation.selected - 1, 0);
    renderCitationSuggestions();
  } else if ((event.key === "Enter" || event.key === "Tab") && state.citation.suggestions.length) {
    event.preventDefault();
    insertCitationSuggestion(state.citation.suggestions[state.citation.selected]);
  } else if (event.key === "Escape") {
    event.preventDefault();
    closeCitationSuggestions();
  }
});
els.body.addEventListener("click", () => {
  const trigger = currentCitationTrigger();
  if (trigger) {
    openCitationSuggestions(trigger);
  } else {
    closeCitationSuggestions();
  }
});
els.body.addEventListener("blur", () => {
  window.setTimeout(closeCitationSuggestions, 120);
});
els.body.addEventListener("scroll", positionCitationSuggestions);
els.toggleBibtexBtn.addEventListener("click", () => {
  els.bibtexPanel.hidden = !els.bibtexPanel.hidden;
  if (!els.bibtexPanel.hidden) {
    els.bibtexInput.focus();
  }
});
els.importBibtexBtn.addEventListener("click", importBibtexEntries);
els.clearBibtexBtn.addEventListener("click", () => {
  els.bibtexInput.value = "";
  els.bibtexStatus.textContent = "Paste one entry or many. I will keep the keys and fill the reference list.";
  els.bibtexInput.focus();
});
els.addReferenceBtn.addEventListener("click", addBlankReference);

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


def normalize_reference_key(value: object) -> str:
    key = str(value or "").strip().lstrip("@")
    key = re.sub(r"[^A-Za-z0-9:_.-]+", "-", key)
    return key.strip("-")


def normalize_references(raw: object) -> list[dict]:
    if not isinstance(raw, list):
        return []
    references: list[dict] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        reference = {
            "key": normalize_reference_key(item.get("key")),
            "author": str(item.get("author") or "").strip(),
            "title": str(item.get("title") or "").strip(),
            "year": str(item.get("year") or "").strip(),
            "venue": str(item.get("venue") or "").strip(),
            "doi": str(item.get("doi") or "").strip(),
            "url": str(item.get("url") or "").strip(),
            "rawBibtex": str(item.get("rawBibtex") or "").strip(),
        }
        if any(reference.values()):
            references.append(reference)
    return references


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
        "references": normalize_references(raw.get("references")),
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


def make_citation_context(references: object) -> dict:
    refs: dict[str, dict] = {}
    for reference in normalize_references(references):
        key = reference.get("key") or ""
        if key and key not in refs:
            refs[key] = reference
    return {"refs": refs, "numbers": {}, "order": [], "missing": set()}


def parse_citation_items(content: str) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    for part in content.split(";"):
        match = re.match(r"\s*@([A-Za-z0-9:_.-]+)(?:\s*,\s*(.+))?\s*$", part)
        if match:
            items.append((match.group(1), (match.group(2) or "").strip()))
    return items


def render_citation(content: str, context: dict | None) -> str:
    if context is None:
        return f"[{content}]"
    items = parse_citation_items(content)
    if not items:
        return f"[{content}]"

    pieces: list[str] = []
    refs = context["refs"]
    numbers = context["numbers"]
    order = context["order"]
    missing = context["missing"]

    for key, locator in items:
        if key not in refs:
            missing.add(key)
            pieces.append(f'<span class="citation-missing">missing @{escape(key)}</span>')
            continue
        if key not in numbers:
            numbers[key] = len(order) + 1
            order.append(key)
        label = str(numbers[key])
        if locator:
            label = f"{label}, {locator}"
        pieces.append(f'<a href="#ref-{escape(key)}">{label}</a>')

    return f'<span class="citation">[{("; ".join(pieces))}]</span>'


def render_inline(text: str, citation_context: dict | None = None) -> str:
    protected, replacements = protect_inline(text)
    rendered = escape(protected)

    def link_repl(match: re.Match[str]) -> str:
        label = match.group(1)
        href = match.group(2)
        if not href.startswith(("http://", "https://", "mailto:", "../", "./", "#", "/")):
            href = "#"
        return f'<a href="{escape(href)}">{label}</a>'

    rendered = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link_repl, rendered)
    rendered = re.sub(
        r"\[((?:@[A-Za-z0-9:_.-]+(?:\s*,\s*[^;@\]]+)?)(?:\s*;\s*@[A-Za-z0-9:_.-]+(?:\s*,\s*[^;@\]]+)?)*)\]",
        lambda match: render_citation(match.group(1), citation_context),
        rendered,
    )
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


def render_markdown(markdown: str, citation_context: dict | None = None) -> str:
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
            output.append(f"<h{level}>{render_inline(heading.group(2).strip(), citation_context)}</h{level}>")
            i += 1
            continue

        if re.match(r"\s*[-*]\s+", line):
            items: list[str] = []
            while i < len(lines) and re.match(r"\s*[-*]\s+", lines[i]):
                item = re.sub(r"^\s*[-*]\s+", "", lines[i]).strip()
                items.append(f"<li>{render_inline(item, citation_context)}</li>")
                i += 1
            output.append(f"<ul>{''.join(items)}</ul>")
            continue

        if re.match(r"\s*\d+\.\s+", line):
            items = []
            while i < len(lines) and re.match(r"\s*\d+\.\s+", lines[i]):
                item = re.sub(r"^\s*\d+\.\s+", "", lines[i]).strip()
                items.append(f"<li>{render_inline(item, citation_context)}</li>")
                i += 1
            output.append(f"<ol>{''.join(items)}</ol>")
            continue

        if line.startswith("> "):
            quote_lines: list[str] = []
            while i < len(lines) and lines[i].startswith("> "):
                quote_lines.append(lines[i][2:].strip())
                i += 1
            output.append(f"<blockquote>{render_inline(' '.join(quote_lines), citation_context)}</blockquote>")
            continue

        paragraph: list[str] = []
        while i < len(lines) and not is_block_start(lines[i]):
            paragraph.append(lines[i].strip())
            i += 1
        output.append(f"<p>{render_inline(' '.join(paragraph), citation_context)}</p>")

    return "\n".join(output) or '<p class="empty-note">No body yet.</p>'


def reference_link(reference: dict) -> tuple[str, str] | None:
    url = str(reference.get("url") or "").strip()
    doi = str(reference.get("doi") or "").strip()
    if url.startswith(("http://", "https://")):
        return ("Link", url)
    if doi:
        href = doi if doi.startswith(("http://", "https://")) else f"https://doi.org/{doi}"
        return ("DOI", href)
    return None


def render_reference_text(reference: dict) -> str:
    parts: list[str] = []
    author = str(reference.get("author") or "").strip()
    title = str(reference.get("title") or "").strip()
    venue = str(reference.get("venue") or "").strip()
    year = str(reference.get("year") or "").strip()
    if author:
        parts.append(f"{escape(author)}.")
    if title:
        parts.append(f'<span class="reference-title">{escape(title)}</span>.')
    if venue:
        parts.append(f"{escape(venue)}.")
    if year:
        parts.append(f"{escape(year)}.")
    link = reference_link(reference)
    if link:
        label, href = link
        parts.append(f'<a class="reference-link" href="{escape(href)}">{escape(label)}</a>.')
    return " ".join(parts) or escape(reference.get("key") or "Untitled reference")


def render_references_section(citation_context: dict) -> str:
    order = citation_context["order"]
    refs = citation_context["refs"]
    if not order:
        return ""
    items = []
    for key in order:
        reference = refs.get(key)
        if not reference:
            continue
        items.append(f'<li id="ref-{escape(key)}">{render_reference_text(reference)}</li>')
    if not items:
        return ""
    return f"""
<section class="references-section">
<h2>References</h2>
<ol class="references-list">
{chr(10).join(items)}
</ol>
</section>
""".strip()


def render_note_article(note: dict) -> str:
    title = escape(note.get("title") or "Untitled note")
    note_date = escape(note.get("date") or "")
    description = escape(note.get("description") or "")
    citation_context = make_citation_context(note.get("references") or [])
    body = render_markdown(note.get("body") or "", citation_context)
    references = render_references_section(citation_context)
    description_html = f'<p class="note-description">{description}</p>' if description else ""
    date_html = f'<span class="note-date">{note_date}</span>' if note_date else ""
    return f"""
<article class="note-article">
<h1>{title}</h1>
{date_html}
{description_html}
<div class="note-body">
{body}
{references}
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

    lede_html = f'\n<p class="lede">{escape(DEFAULT_LEDE)}</p>' if DEFAULT_LEDE else ""

    body = f"""
<div class="page">
<nav aria-label="Site links" class="topline">
<a href="../index.html">Home</a>
</nav>
<header>
<h1>Notes</h1>{lede_html}
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
        if relative_path == Path("."):
            relative_path = Path("index.html")
        if relative_path == Path("notes"):
            relative_path = Path("notes/index.html")
        if not self.is_public_site_path(relative_path):
            self.send_text(403, "Forbidden")
            return
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

    @staticmethod
    def is_public_site_path(relative_path: Path) -> bool:
        parts = relative_path.parts
        if len(parts) == 1:
            return parts[0] in PUBLIC_ROOT_FILES
        if len(parts) == 2 and parts[0] == "notes":
            return parts[1].endswith(".html")
        return False


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
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PORT_FILE.write_text(str(actual_port), encoding="utf-8")
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
        try:
            PORT_FILE.unlink()
        except FileNotFoundError:
            pass


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
