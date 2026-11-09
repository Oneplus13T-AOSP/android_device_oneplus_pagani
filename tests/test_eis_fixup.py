#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Run against the extracted COS17 libEIS.so; no extraction/build-tree writes."""
import ast
from pathlib import Path
import sys
import tempfile
import unittest

BLOB = Path(sys.argv.pop(1)).read_bytes()
SOURCE = Path(__file__).resolve().parents[1] / 'extract-files.py'
node = next(node for node in ast.parse(SOURCE.read_text()).body
            if isinstance(node, ast.FunctionDef) and node.name == 'fixup_eis_snap_handle_format')
namespace = {'Path': Path}
exec(compile(ast.Module(body=[node], type_ignores=[]), str(SOURCE), 'exec'), namespace)
fixup = namespace[node.name]


class EisFixupTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'libEIS.so'
        self.path.write_bytes(BLOB)

    def test_five_audited_format_loads_only(self):
        fixup(None, None, self.path)
        result = self.path.read_bytes()
        self.assertEqual(len(result), len(BLOB))
        changed = [i for i, (old, new) in enumerate(zip(BLOB, result)) if old != new]
        self.assertEqual(changed, [0x13525, 0x2158d, 0x21739, 0x21c11, 0x21d45])
        # Decode the AArch64 LDR immediate. Every changed load now reads 0x34.
        for offset in changed:
            instruction = int.from_bytes(result[offset - 1:offset + 3], 'little')
            self.assertEqual(((instruction >> 10) & 0xfff) * 4, 0x34)

    def test_idempotent(self):
        fixup(None, None, self.path)
        first = self.path.read_bytes()
        fixup(None, None, self.path)
        self.assertEqual(self.path.read_bytes(), first)

    def test_unknown_build_rejected_before_writing(self):
        damaged = bytearray(BLOB)
        damaged[0x21d4c] ^= 1  # Break the final call anchor, after four valid sites.
        self.path.write_bytes(damaged)
        with self.assertRaises(ValueError):
            fixup(None, None, self.path)
        self.assertEqual(self.path.read_bytes(), damaged)

    def test_duplicate_anchor_rejected_before_writing(self):
        data = BLOB + BLOB[0x13524:0x13538]
        self.path.write_bytes(data)
        with self.assertRaises(ValueError):
            fixup(None, None, self.path)
        self.assertEqual(self.path.read_bytes(), data)


if __name__ == '__main__':
    unittest.main()
