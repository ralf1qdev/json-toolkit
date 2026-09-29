# JSON Toolkit

A local Python utility for validating, formatting, minifying, and comparing JSON.
Use the desktop window or run commands in your terminal. No third-party Python packages, accounts, or network connection required.

## Start here

Requires Python 3.9 or newer. Desktop mode also requires Tkinter, included in many Python installations. On Windows, keep the Tcl/Tk option enabled when installing Python.

1. Download and extract this project.
2. Open a terminal in the extracted `json-toolkit` folder.
3. Start the app:

```sh
python json_toolkit.py
```

On Windows you can use `py` instead of `python`; on macOS/Linux you may need `python3`.
If Tkinter is unavailable, the terminal commands still work.

## Desktop design

The desktop workspace uses a midnight palette with blue accents, syntax highlighting, line numbers, live document counts, adjustable side-by-side editors, and colored comparison results.

- **Copy result** copies the right editor to the clipboard.
- **Ctrl+O** opens a file, **Ctrl+Enter** formats, and **Ctrl+S** saves the result.
- Validation errors appear in the status area without interrupting editing.
- Highlighting is disabled above 150,000 characters to keep larger documents responsive.

## Desktop workflow

- Paste JSON into the left editor, or choose **Open**.
- **Validate** checks syntax, duplicate keys, and invalid constants.
- **Format**, **Minify**, or **Sort keys** writes the result to the right editor.
- **Save result** exports the right editor to a file; the file picker asks before overwriting.
- To **Compare**, paste the second JSON document into the right editor. A separate window shows the differences without replacing either document.

JSON syntax errors include the line and column. Duplicate-key errors identify the key.

## Terminal commands

```sh
python json_toolkit.py validate examples/settings.json
python json_toolkit.py format examples/settings.json
python json_toolkit.py format examples/settings.json --sort-keys -o formatted.json
python json_toolkit.py minify examples/settings.json -o compact.json
python json_toolkit.py compare examples/settings.json examples/settings-updated.json
```

Formatting and minifying print to the terminal unless `-o` is supplied. Output files are created only if the destination does not exist, protecting existing data.
Use `-` as the input filename to read from standard input.

Exit codes: **0** success or no differences; **1** comparison found differences; **2** invalid input or another error.

## Data handling

- Files stay on your computer; the program makes no network requests.
- Numbers use decimal arithmetic during parsing, avoiding binary-float precision loss.
- Formatting can normalize number notation and escape Unicode characters without changing their values.
- Comparison ignores object-key order and whitespace, preserves array order, and compares formatted values. Numeric representations such as `1` and `1.0` may appear as differences.
- Duplicate keys, `NaN`, and `Infinity` are rejected rather than silently accepted.
- Input is UTF-8 (an optional UTF-8 BOM is accepted when opening files).
- This is an in-memory tool for everyday configuration files, not a streaming processor for huge datasets. Very large or deeply nested input may exceed available resources.

## Checks

```sh
python -m unittest discover -s tests -v
```

## Put it on GitHub

1. Create a public repository named `json-toolkit`.
2. Choose **uploading an existing file**, or **Add file → Upload files**.
3. Upload the extracted project contents, including `json_toolkit.py`, this README, `examples`, and `tests`. Do not upload only the ZIP.
4. Commit the files, then add the repository to your profile's pinned projects.

Suggested repository description: **Local JSON validator, formatter, minifier, and comparison tool built with Python.**

No license has been selected. Add a license before inviting reuse under specific open-source terms.
