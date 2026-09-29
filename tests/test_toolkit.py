import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from decimal import Decimal
from json_toolkit import JSONProblem, compare, main, parse, transform


class ToolkitTests(unittest.TestCase):
    def test_error_location(self):
        with self.assertRaisesRegex(JSONProblem, 'Line 2, column'):
            parse('{\n"x": }')

    def test_duplicate_and_nonstandard_values(self):
        for value in ('{"x":1,"x":2}', 'NaN', 'Infinity', '-Infinity'):
            with self.subTest(value=value), self.assertRaises(JSONProblem):
                parse(value)

    def test_precision_and_roundtrip(self):
        text = '{"n":0.12345678901234567890123456789,"big":1e400,"text":"こんにちは","items":[true,null,{"a":2}]}'
        for compact in (True, False):
            self.assertEqual(parse(text), parse(transform(text, compact)))
        self.assertEqual(parse(transform(text))['n'], Decimal('0.12345678901234567890123456789'))

    def test_comparison(self):
        self.assertEqual(compare('{"b":2,"a":1}', '{"a":1,"b":2}'), '')
        self.assertIn('-  true', compare('[true]', '[1]'))
        self.assertTrue(compare('[1,2]', '[2,1]'))

    def test_cli_and_overwrite_protection(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'input.json'
            output = Path(directory) / 'output.json'
            source.write_text('{"a":1}', encoding='utf-8')
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(['validate', str(source)]), 0)
                self.assertEqual(main(['format', str(source), '-o', str(output)]), 0)
                original = output.read_bytes()
                self.assertEqual(main(['minify', str(source), '-o', str(output)]), 2)
                self.assertEqual(output.read_bytes(), original)
                self.assertEqual(main(['compare', str(source), str(output)]), 0)
                self.assertEqual(main(['validate', str(source) + '.missing']), 2)


if __name__ == '__main__':
    unittest.main()
