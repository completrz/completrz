#!/usr/bin/env python3
"""Apply stable presentation tweaks to GitAscii-generated profile SVGs."""
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

# Matches one top-level GitAscii widget, whose end tag has four spaces of indentation.
WIDGET = re.compile(r'(?P<open>    <g transform="translate\([^\n]+?" id="widget-[^\n]+">)(?P<body>.*?)(?P<close>\n    </g>)', re.S)
BAR = re.compile(r'<rect\s+x="([\d.]+)"\s+y="52"\s+width="([\d.]+)"\s+height="8"\s+fill="(#[\da-fA-F]+)"\s+rx="2"\s*/>')
LEGEND = re.compile(r'<g transform="translate\((\d+),\s*(\d+)\)">\s*<circle[^>]*fill="(#[\da-fA-F]+)"[^>]*/>\s*<text[^>]*>([^<]+)</text>\s*</g>', re.S)


def change_widget(m):
    body = m['body']
    if '[ TOP LANGUAGES ]' in body:
        bars = list(BAR.finditer(body))
        legends = list(LEGEND.finditer(body))
        if bars and len(bars) == len(legends):
            entries = []
            for b, l in zip(bars, legends):
                name = l.group(4).strip()
                entries.append((name, float(b.group(2)), COLORS.get(name, b.group(3))))
            entries.sort(key=lambda e: (ORDER.index(e[0]) if e[0] in ORDER else len(ORDER)))
            x = float(bars[0].group(1))
            new_bars = []
            new_legends = []
            for i, (name, width, color) in enumerate(entries):
                new_bars.append(f'<rect x="{x:g}" y="52" width="{width:g}" height="8" fill="{color}" rx="2"/>')
                x += width
                lx, ly = (24 if i % 2 == 0 else 268), 80 + 24 * (i // 2)
                new_legends.append(f'<g transform="translate({lx}, {ly})"><circle cx="6" cy="-4" r="4" fill="{color}"/><text x="16" y="0" font-family="\'Inter Tight\', sans-serif" font-size="12" fill="#e5e5e5">{escape(name)} </text></g>')
            # Reverse-order replacement preserves match offsets.
            changes = [(b.start(), b.end(), t) for b, t in zip(bars, new_bars)]
            changes += [(l.start(), l.end(), t) for l, t in zip(legends, new_legends)]
            for start, end, replacement in sorted(changes, reverse=True):
                body = body[:start] + replacement + body[end:]
    if ' Contact ' in body and 'GitHub Stats' in body:
        # Remove previous custom additions on reruns, but keep native GitAscii stats.
        body = re.sub(r'\s*<g id="custom-contact-links">.*?</g>', '', body, flags=re.S).rstrip()
        lines = ['\n<g id="custom-contact-links">']
        for i, (label, display, url) in enumerate(CONTACT):
            y = 185 + i * 22
            lines.append(f'<text x="12" y="{y}" font-family="Consolas, Menlo, JetBrains Mono, monospace" font-size="12"><tspan fill="#52c85f">. {escape(label)}: </tspan><a href="{escape(url, quote=True)}"><tspan fill="#8ab4f8">{escape(display)}</tspan></a></text>')
        lines.append('</g>')
        body += '\n'.join(lines) + '\n'
    return m['open'] + body + m['close']


for path in sorted(Path('profiles').glob('**/*.svg')):
    original = path.read_text(encoding='utf-8')
    changed = WIDGET.sub(change_widget, original)
    if changed != original:
        path.write_text(changed, encoding='utf-8')
        print('Customized', path)
