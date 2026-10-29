#!/usr/bin/env python3
"""Keep GitAscii language colors/order and integrate contact rows into its native animation."""
from pathlib import Path
import re
from html import escape

ORDER = ['Jupyter Notebook', 'R', 'HTML', 'Python']
COLORS = {'R': '#276DC3'}
CONTACT = [
    ('LinkedIn', 'linkedin.com/in/nicholas-hinkel', 'https://www.linkedin.com/in/nicholas-hinkel'),
    ('Website', 'nicholashinkel.com', 'https://nicholashinkel.com'),
    ('Email', 'hinkel.nicholas12@gmail.com', 'mailto:hinkel.nicholas12@gmail.com'),
]

WIDGET = re.compile(r'(?P<open>    <g transform="translate\([^\n]+?" id="widget-[^\n]+">)(?P<body>.*?)(?P<close>\n    </g>)', re.S)
BAR = re.compile(r'<rect\s+x="([\d.]+)"\s+y="52"\s+width="([\d.]+)"\s+height="8"\s+fill="(#[\da-fA-F]+)"\s+rx="2"\s*/>')
LEGEND = re.compile(r'<g transform="translate\((\d+),\s*(\d+)\)">\s*<circle[^>]*fill="(#[\da-fA-F]+)"[^>]*/>\s*<text[^>]*>([^<]+)</text>\s*</g>', re.S)

def animated_row(label, display, url, y, delay):
    """Use GitAscii's anim-target class and delayed tspan reveal, not static overlay text."""
    label_text = f'. {label}: '
    # Small font fits the long LinkedIn and email URLs inside the 504px widget.
    dots = '.' * max(0, 57 - len(label_text) - len(display) - 1)
    return (
        f'<text class="anim-target" x="12" y="{y}" '
        f'font-family="\'Consolas\', \'Menlo\', \'DejaVu Sans Mono\', \'JetBrains Mono\', monospace" '
        f'xml:space="preserve" font-size="14" '
        f'style="animation-delay: {delay}ms; transform-origin: center;">'
        f'<tspan class="anim-target" fill="#52c85f" '
        f'style="animation-delay: {delay+21}ms; transform-origin: center;">{escape(label_text)}</tspan>'
        f'<tspan class="anim-target" fill="#484f58" '
        f'style="animation-delay: {delay+42}ms; transform-origin: center;">{dots}</tspan>'
        f'<a href="{escape(url, quote=True)}" target="_blank">'
        f'<tspan class="anim-target" fill="#c9d1d9" '
        f'style="animation-delay: {delay+63}ms; transform-origin: center;"> {escape(display)}</tspan>'
        f'</a></text>'
    )

def change_widget(m):
    body = m['body']
    if '[ TOP LANGUAGES ]' in body:
        bars, legends = list(BAR.finditer(body)), list(LEGEND.finditer(body))
        if bars and len(bars) == len(legends):
            entries = [(l.group(4).strip(), float(b.group(2)),
                        COLORS.get(l.group(4).strip(), b.group(3)))
                       for b, l in zip(bars, legends)]
            entries.sort(key=lambda e: ORDER.index(e[0]) if e[0] in ORDER else len(ORDER))
            x = float(bars[0].group(1))
            replacements = []
            for i, (name, width, color) in enumerate(entries):
                replacements.append((bars[i].start(), bars[i].end(),
                    f'<rect x="{x:g}" y="52" width="{width:g}" height="8" fill="{color}" rx="2"/>'))
                x += width
                lx, ly = (24 if i % 2 == 0 else 268), 80 + 24 * (i // 2)
                replacements.append((legends[i].start(), legends[i].end(),
                    f'<g transform="translate({lx}, {ly})"><circle cx="6" cy="-4" r="4" fill="{color}"/>'
                    f'<text x="16" y="0" font-family="\'Inter Tight\', sans-serif" font-size="12" fill="#e5e5e5">{escape(name)} </text></g>'))
            for start, end, replacement in sorted(replacements, reverse=True):
                body = body[:start] + replacement + body[end:]

    if ' Contact ' in body and 'GitHub Stats' in body:
        # Remove any previous custom contact group (safe to rerun).
        body = re.sub(r'\s*<g id="custom-contact-links">.*?</g>', '', body, flags=re.S)
        # Reset/position native stats rows so running this repeatedly never moves them further.
        # Identify native text lines by their visible content rather than global y replacement.
        lines = body.splitlines()
        for i, line in enumerate(lines):
            if ' GitHub Stats ' in line:
                lines[i] = re.sub(r'\by="\d+"', 'y="180"', line, count=1)
            elif '. Repos: ' in line:
                lines[i] = re.sub(r'\by="\d+"', 'y="198"', line, count=1)
        body = '\n'.join(lines)
        # Insert contact lines immediately after native GitHub row, inside the same animated widget.
        custom = '\n'.join(animated_row(label, display, url, 120 + 20*i, 430 + 85*i)
                           for i, (label, display, url) in enumerate(CONTACT))
        body = re.sub(r'(<text\b[^\n]*\. GitHub: [^\n]*</text>)',
                      lambda match: match.group(1) + '\n' + custom,
                      body, count=1)
    return m['open'] + body + m['close']

for path in sorted(Path('profiles').glob('**/*.svg')):
    original = path.read_text(encoding='utf-8')
    changed = WIDGET.sub(change_widget, original)
    if changed != original:
        path.write_text(changed, encoding='utf-8')
        print('Customized', path)
