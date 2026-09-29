#!/usr/bin/env python3
"""Local JSON utilities. No third-party packages required."""
import argparse
import difflib
import json
import sys
from decimal import Decimal
from pathlib import Path


class JSONProblem(ValueError):
    pass


def reject_constant(value):
    raise JSONProblem(f'{value} is not valid JSON.')


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise JSONProblem(f'Duplicate object key: {key!r}')
        result[key] = value
    return result


def parse(text):
    try:
        return json.loads(text, parse_float=Decimal, parse_int=Decimal,
                          parse_constant=reject_constant, object_pairs_hook=unique_object)
    except json.JSONDecodeError as exc:
        raise JSONProblem(f'Line {exc.lineno}, column {exc.colno}: {exc.msg}') from exc


def encode(value, indent=2, sort=False, level=0):
    """Serialize without converting precise JSON numbers to binary floats."""
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (dict, list)):
        is_object = isinstance(value, dict)
        opening, closing = ('{', '}') if is_object else ('[', ']')
        if not value:
            return opening + closing
        items = []
        iterable = sorted(value) if is_object and sort else value
        for key in iterable:
            item = value[key] if is_object else key
            prefix = (json.dumps(key, ensure_ascii=True) + (': ' if indent else ':')) if is_object else ''
            items.append(prefix + encode(item, indent, sort, level + 1))
        if not indent:
            return opening + ','.join(items) + closing
        padding = ' ' * (indent * (level + 1))
        return opening + '\n' + padding + (',\n' + padding).join(items) + '\n' + ' ' * (indent * level) + closing
    return json.dumps(value, ensure_ascii=True, allow_nan=False)


def transform(text, compact=False, sort=False):
    return encode(parse(text), 0 if compact else 2, sort) + '\n'


def compare(left, right):
    # Canonical key ordering ignores object-key order, but preserves array order.
    a = (encode(parse(left), sort=True) + '\n').splitlines(keepends=True)
    b = (encode(parse(right), sort=True) + '\n').splitlines(keepends=True)
    return ''.join(difflib.unified_diff(a, b, fromfile='left', tofile='right', lineterm='\n'))


def read_file(path):
    return Path(path).read_text(encoding='utf-8-sig')


def launch_gui():
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox, ttk, font as tkfont
        import re
    except ImportError:
        print('Desktop mode needs Tkinter. Use the CLI, or install Python with Tcl/Tk support.', file=sys.stderr)
        return 2
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        print(f'Cannot open a desktop window: {exc}. Use a command-line command instead.', file=sys.stderr)
        return 2

    colors = dict(bg='#0b1018', panel='#111925', editor='#0e1621', line='#253245',
                  text='#e6edf6', muted='#8d9db2', accent='#7c9cff', green='#69d6b0', red='#ff8595')
    families = set(tkfont.families(root))
    ui = 'Segoe UI' if 'Segoe UI' in families else 'DejaVu Sans'
    mono = 'Cascadia Code' if 'Cascadia Code' in families else ('Consolas' if 'Consolas' in families else 'DejaVu Sans Mono')
    root.title('JSON Toolkit')
    root.geometry('1180x780')
    root.minsize(940, 600)
    root.configure(bg=colors['bg'])
    root.option_add('*Font', (ui, 10))
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('Vertical.TScrollbar', background='#29374c', troughcolor=colors['editor'], borderwidth=0, arrowsize=12)
    style.configure('Horizontal.TScrollbar', background='#29374c', troughcolor=colors['editor'], borderwidth=0, arrowsize=12)
    style.map('Vertical.TScrollbar', background=[('active', '#445878')])
    style.map('Horizontal.TScrollbar', background=[('active', '#445878')])

    def label(parent, text, size=10, color='text', bold=False, bg=None):
        return tk.Label(parent, text=text, bg=bg or parent.cget('bg'), fg=colors.get(color, color),
                        font=(ui, size, 'bold' if bold else 'normal'), anchor='w')

    def button(parent, text, command, primary=False):
        normal = colors['accent'] if primary else '#1b283b'
        hover = '#96afff' if primary else '#2a3b54'
        widget = tk.Button(parent, text=text, command=command, bg=normal,
                           fg='#0b1018' if primary else colors['text'], activebackground=hover,
                           activeforeground='#0b1018' if primary else colors['text'],
                           relief='flat', bd=0, padx=15, pady=9, cursor='hand2',
                           highlightthickness=1, highlightbackground=normal,
                           highlightcolor=colors['accent'], font=(ui, 10, 'bold' if primary else 'normal'))
        widget.bind('<Enter>', lambda _: widget.configure(bg=hover))
        widget.bind('<Leave>', lambda _: widget.configure(bg=normal))
        return widget

    header = tk.Frame(root, bg=colors['bg'])
    header.pack(fill='x', padx=26, pady=(23, 18))
    mark = tk.Label(header, text='{ }', bg='#1d2b46', fg=colors['accent'], font=(mono, 20, 'bold'), padx=13, pady=6)
    mark.pack(side='left', padx=(0, 14))
    brand = tk.Frame(header, bg=colors['bg'])
    brand.pack(side='left')
    label(brand, 'JSON Toolkit', 22, bold=True).pack(anchor='w')
    label(brand, 'Less noise. Better JSON.', 10, 'muted').pack(anchor='w', pady=(2, 0))
    label(header, '●  LOCAL PROCESSING', 9, 'green').pack(side='right')

    toolbar = tk.Frame(root, bg=colors['panel'], highlightbackground=colors['line'], highlightthickness=1)
    toolbar.pack(fill='x', padx=26, pady=(0, 20))
    tools = tk.Frame(toolbar, bg=colors['panel'])
    tools.pack(side='left', padx=12, pady=12)
    file_tools = tk.Frame(toolbar, bg=colors['panel'])
    file_tools.pack(side='right', padx=12, pady=12)

    heading = tk.Frame(root, bg=colors['bg'])
    heading.pack(fill='x', padx=26, pady=(0, 12))
    label(heading, 'Workspace', 13, bold=True).pack(side='left')
    label(heading, 'Format on the left → results on the right', 10, 'muted').pack(side='right')
    panels = tk.PanedWindow(root, orient='horizontal', bg=colors['bg'], sashwidth=14,
                           sashrelief='flat', bd=0, opaqueresize=True)
    panels.pack(fill='both', expand=True, padx=26)
    editors, counters, gutters = [], [], []
    pending = {}
    token = re.compile(r'"(?:\\.|[^"\\])*"|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|\b(?:true|false|null)\b')

    def content(editor):
        return editor.get('1.0', 'end-1c')

    def draw_lines(editor, canvas):
        canvas.delete('all')
        index = editor.index('@0,0')
        while True:
            box = editor.dlineinfo(index)
            if box is None:
                break
            canvas.create_text(39, box[1], anchor='ne', text=index.split('.')[0],
                               fill='#52647d', font=(mono, 11))
            index = editor.index(f'{index}+1line')

    key_suffix = re.compile(r'\s*:')

    def refresh(editor, counter, canvas):
        pending.pop(editor, None)
        text = content(editor)
        counter.set(f'{text.count(chr(10)) + 1:,} lines  ·  {len(text):,} characters')
        for tag in ('key', 'string', 'number', 'literal'):
            editor.tag_remove(tag, '1.0', 'end')
        # Bound highlighting work for large documents; all text remains editable.
        if len(text) <= 150000:
            for match in token.finditer(text):
                value = match.group()
                if value.startswith('"'):
                    tag = 'key' if key_suffix.match(text, match.end()) is not None else 'string'
                else:
                    tag = 'literal' if value in ('true', 'false', 'null') else 'number'
                editor.tag_add(tag, f'1.0+{match.start()}c', f'1.0+{match.end()}c')
        draw_lines(editor, canvas)

    def schedule(editor, counter, canvas):
        if editor in pending:
            root.after_cancel(pending[editor])
        pending[editor] = root.after(160, lambda: refresh(editor, counter, canvas))

    for title, subtitle in [('SOURCE', 'Paste JSON or open a file'), ('RESULT', 'Output · or paste a second JSON to compare')]:
        card = tk.Frame(panels, bg=colors['panel'], highlightbackground=colors['line'], highlightthickness=1)
        top = tk.Frame(card, bg=colors['panel'])
        top.pack(fill='x', padx=16, pady=(15, 13))
        label(top, title, 10, 'accent', True).pack(anchor='w')
        label(top, subtitle, 9, 'muted').pack(anchor='w', pady=(5, 0))
        body = tk.Frame(card, bg=colors['editor'])
        body.pack(fill='both', expand=True)
        body.rowconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        gutter = tk.Canvas(body, width=49, bg=colors['editor'], highlightthickness=0)
        gutter.grid(row=0, column=0, sticky='ns')
        editor = tk.Text(body, wrap='none', undo=True, bg=colors['editor'], fg=colors['text'],
                         insertbackground=colors['accent'], selectbackground='#304b78', selectforeground='#ffffff',
                         font=(mono, 11), relief='flat', bd=0, padx=8, pady=10, spacing1=2, spacing3=2,
                         highlightthickness=0)
        editor.grid(row=0, column=1, sticky='nsew')
        vertical = ttk.Scrollbar(body, orient='vertical', command=editor.yview)
        vertical.grid(row=0, column=2, sticky='ns')
        horizontal = ttk.Scrollbar(body, orient='horizontal', command=editor.xview)
        horizontal.grid(row=1, column=1, sticky='ew')
        def scroll(first, last, e=editor, g=gutter, bar=vertical):
            bar.set(first, last)
            draw_lines(e, g)
        editor.configure(yscrollcommand=scroll, xscrollcommand=horizontal.set)
        for tag, color in [('key', '#91b9ff'), ('string', '#8edbb8'), ('number', '#eabd86'), ('literal', '#c5a3ff')]:
            editor.tag_configure(tag, foreground=color)
        counter = tk.StringVar(value='1 lines  ·  0 characters')
        footer = tk.Frame(card, bg=colors['panel'])
        footer.pack(fill='x', padx=16, pady=10)
        tk.Label(footer, textvariable=counter, bg=colors['panel'], fg=colors['muted'], font=(ui, 9)).pack(side='left')
        label(footer, 'JSON', 9, 'muted').pack(side='right')
        def modified(event, e=editor, c=counter, g=gutter):
            if e.edit_modified():
                e.edit_modified(False)
                schedule(e, c, g)
        editor.bind('<<Modified>>', modified)
        editor.bind('<Configure>', lambda event, e=editor, g=gutter: draw_lines(e, g))
        panels.add(card, minsize=330, stretch='always')
        editors.append(editor)
        counters.append(counter)
        gutters.append(gutter)
    source, output = editors
    source.insert('1.0', '{\n  "project": "JSON Toolkit",\n  "theme": "midnight",\n  "local": true,\n  "tools": ["format", "validate", "compare"]\n}')

    bottom = tk.Frame(root, bg=colors['bg'])
    bottom.pack(fill='x', padx=26, pady=(14, 18))
    status = tk.StringVar(value='Ready. Your JSON stays on this device.')
    status_label = tk.Label(bottom, textvariable=status, anchor='w', bg=colors['bg'], fg=colors['muted'], font=(ui, 10))
    status_label.pack(fill='x')
    bottom.bind('<Configure>', lambda event: status_label.configure(wraplength=max(200, event.width - 12)))
    label(bottom, 'Ctrl+O  Open     Ctrl+Enter  Format     Ctrl+S  Save result', 9, 'muted').pack(anchor='w', pady=(7, 0))

    def report(text, error=False):
        status.set(text)
        status_label.configure(fg=colors['red'] if error else colors['green'])

    def run(action):
        try:
            if action == 'Validate':
                parse(content(source))
                report('Valid JSON · No duplicate keys or invalid constants.')
                return
            if action == 'Compare':
                result = compare(content(source), content(output))
                window = tk.Toplevel(root)
                window.title('JSON Toolkit · Comparison')
                window.geometry('860x570')
                window.configure(bg=colors['bg'])
                label(window, 'Comparison', 19, bold=True).pack(anchor='w', padx=20, pady=(20, 5))
                label(window, 'Object key order is ignored. Array order is preserved.', 10, 'muted').pack(anchor='w', padx=20, pady=(0, 16))
                from tkinter.scrolledtext import ScrolledText
                view = ScrolledText(window, wrap='none', font=(mono, 11), bg=colors['editor'], fg=colors['text'],
                                    insertbackground=colors['accent'], relief='flat', padx=15, pady=15)
                view.pack(fill='both', expand=True, padx=20, pady=(0, 20))
                view.tag_configure('added', foreground=colors['green'])
                view.tag_configure('removed', foreground=colors['red'])
                view.tag_configure('header', foreground=colors['accent'])
                for line in (result or 'No differences.').splitlines(keepends=True):
                    tag = 'header' if line.startswith(('+++', '---', '@@')) else ('added' if line.startswith('+') else ('removed' if line.startswith('-') else ''))
                    view.insert('end', line, tag)
                view.configure(state='disabled')
                report('Comparison opened · Both documents preserved.')
                return
            result = transform(content(source), compact=action == 'Minify', sort=action == 'Sort keys')
            output.delete('1.0', 'end')
            output.insert('1.0', result.rstrip('\n'))
            report(f'{action} complete · Result ready to copy or save.')
        except (ValueError, RecursionError) as exc:
            report(f'Error · {exc}', True)

    def open_json():
        path = filedialog.askopenfilename(parent=root, filetypes=[('JSON', '*.json'), ('All files', '*.*')])
        if path:
            try:
                text = read_file(path)
                source.delete('1.0', 'end')
                source.insert('1.0', text)
                report(f'Opened · {Path(path).name}')
            except (OSError, UnicodeError) as exc:
                report(f'Open failed · {exc}', True)

    def save_output():
        text = content(output)
        try:
            parse(text)
        except (ValueError, RecursionError) as exc:
            report(f'Cannot save · {exc}', True)
            return
        path = filedialog.asksaveasfilename(parent=root, defaultextension='.json', filetypes=[('JSON', '*.json')])
        if path:
            try:
                Path(path).write_text(text, encoding='utf-8')
                report(f'Saved · {Path(path).name}')
            except OSError as exc:
                report(f'Save failed · {exc}', True)

    def copy_output():
        if not content(output):
            report('Nothing to copy · Format a document first.', True)
            return
        root.clipboard_clear()
        root.clipboard_append(content(output))
        report('Result copied to clipboard.')

    for action in ('Format', 'Validate', 'Minify', 'Sort keys', 'Compare'):
        button(tools, action, lambda a=action: run(a), primary=action == 'Format').pack(side='left', padx=(0, 6))
    button(file_tools, 'Open file', open_json).pack(side='left', padx=(0, 6))
    button(file_tools, 'Save result', save_output).pack(side='left')
    button(heading, 'Copy result', copy_output).pack(side='right', padx=(0, 14))
    for sequence, callback in [('<Control-o>', open_json), ('<Control-s>', save_output), ('<Control-Return>', lambda: run('Format'))]:
        root.bind(sequence, lambda event, fn=callback: (fn(), 'break')[1])
    root.after(100, lambda: panels.sash_place(0, max(330, panels.winfo_width() // 2), 0))
    source.focus_set()
    root.mainloop()
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command')
    sub.add_parser('gui', help='Open the desktop app (also the default)')
    for command in ('validate', 'format', 'minify'):
        child = sub.add_parser(command)
        child.add_argument('file', help='UTF-8 JSON file; use - for standard input')
        if command != 'validate':
            child.add_argument('-o', '--output', help='New output file (existing files are never overwritten)')
            child.add_argument('--sort-keys', action='store_true')
    diff = sub.add_parser('compare', help='Compare parsed JSON, ignoring object-key order')
    diff.add_argument('left')
    diff.add_argument('right')
    args = parser.parse_args(argv)
    if args.command in (None, 'gui'):
        return launch_gui()
    try:
        if args.command == 'compare':
            result = compare(read_file(args.left), read_file(args.right))
            sys.stdout.write(result or 'No differences.\n')
            return 1 if result else 0
        text = sys.stdin.read() if args.file == '-' else read_file(args.file)
        if args.command == 'validate':
            parse(text)
            print('Valid JSON.')
        else:
            result = transform(text, args.command == 'minify', args.sort_keys)
            if args.output:
                with open(args.output, 'x', encoding='utf-8', newline='\n') as handle:
                    handle.write(result)
            else:
                sys.stdout.write(result)
        return 0
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
