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
        from tkinter import filedialog, messagebox, ttk
        from tkinter.scrolledtext import ScrolledText
    except ImportError:
        print('Desktop mode needs Tkinter. Use the CLI, or install Python with Tcl/Tk support.', file=sys.stderr)
        return 2
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        print(f'Cannot open a desktop window: {exc}. Use a command-line command instead.', file=sys.stderr)
        return 2
    root.title('JSON Toolkit')
    root.geometry('1100x720')
    root.minsize(760, 480)
    root.configure(bg='#0d1117')
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('TFrame', background='#0d1117')
    style.configure('TLabel', background='#0d1117', foreground='#c9d1d9')
    style.configure('TButton', padding=(12, 8))
    toolbar = ttk.Frame(root, padding=12)
    toolbar.pack(fill='x')
    ttk.Label(toolbar, text='JSON TOOLKIT', font=('Arial', 16, 'bold')).pack(side='left', padx=(0, 24))
    status = tk.StringVar(value='Paste JSON on the left. All processing stays on your computer.')
    panels = ttk.Panedwindow(root, orient='horizontal')
    panels.pack(fill='both', expand=True, padx=12)
    editors = []
    for title in ('INPUT', 'OUTPUT / SECOND JSON FOR COMPARE'):
        panel = ttk.Frame(panels)
        ttk.Label(panel, text=title, padding=(0, 8)).pack(anchor='w')
        editor = ScrolledText(panel, wrap='none', undo=True, bg='#161b22', fg='#e6edf3',
                              insertbackground='#58a6ff', font=('Courier', 11), relief='flat')
        editor.pack(fill='both', expand=True)
        panels.add(panel, weight=1)
        editors.append(editor)
    source, output = editors
    source.insert('1.0', '{\n  "project": "JSON Toolkit",\n  "ready": true\n}')
    ttk.Label(root, textvariable=status, padding=12, wraplength=1000).pack(fill='x')

    def content(editor):
        return editor.get('1.0', 'end-1c')

    def run(action):
        try:
            if action == 'Validate':
                parse(content(source))
                status.set('Valid JSON. No duplicate keys or non-standard numeric constants.')
                return
            if action == 'Compare':
                result = compare(content(source), content(output))
                window = tk.Toplevel(root)
                window.title('JSON comparison')
                window.geometry('800x500')
                view = ScrolledText(window, wrap='none', font=('Courier', 11))
                view.pack(fill='both', expand=True)
                view.insert('1.0', result or 'No differences. Object key order is ignored.')
                view.configure(state='disabled')
                status.set('Comparison opened; both editors preserved.')
                return
            result = transform(content(source), compact=action == 'Minify', sort=action == 'Sort keys')
            output.delete('1.0', 'end')
            output.insert('1.0', result)
            status.set(f'{action} complete. Save output to export it.')
        except (ValueError, RecursionError) as exc:
            status.set(f'Error: {exc}')
            messagebox.showerror('JSON error', str(exc), parent=root)

    def open_json():
        path = filedialog.askopenfilename(filetypes=[('JSON', '*.json'), ('All files', '*.*')])
        if path:
            try:
                text = read_file(path)
                source.delete('1.0', 'end')
                source.insert('1.0', text)
                status.set(f'Opened {Path(path).name}')
            except (OSError, UnicodeError) as exc:
                messagebox.showerror('Open failed', str(exc), parent=root)

    def save_output():
        text = content(output)
        try:
            parse(text)
        except (ValueError, RecursionError) as exc:
            messagebox.showerror('Output is not valid JSON', str(exc), parent=root)
            return
        path = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON', '*.json')])
        if path:
            try:
                Path(path).write_text(text, encoding='utf-8')
                status.set(f'Saved {Path(path).name}')
            except OSError as exc:
                messagebox.showerror('Save failed', str(exc), parent=root)

    ttk.Button(toolbar, text='Open', command=open_json).pack(side='left', padx=3)
    for action in ('Validate', 'Format', 'Minify', 'Sort keys', 'Compare'):
        ttk.Button(toolbar, text=action, command=lambda a=action: run(a)).pack(side='left', padx=3)
    ttk.Button(toolbar, text='Save output', command=save_output).pack(side='left', padx=3)
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
