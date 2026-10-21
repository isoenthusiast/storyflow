import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from tools.backup import copy_database
from tools.demo import seed
from webapp.server import Store


class BackupTests(unittest.TestCase):
    def test_live_backup_restore_retains_full_history_and_can_be_edited(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            item = seed(root / 'live.db')
            live = Store(root / 'live.db')
            backup = copy_database(root / 'live.db', root / 'backup.db')
            live.save({'version': item['version'], 'title': 'Later change'}, item['id'])
            restored = Store(copy_database(backup, root / 'restored.db'))
            self.assertEqual(restored.all(), [item])
            self.assertEqual(len(restored.history(item['id'])), 2)
            self.assertEqual(len(restored.activity(item['id'])), 3)
            changed = restored.save({'version': item['version'], 'title': 'Recovered'}, item['id'])
            self.assertEqual(changed['version'], 4)
            self.assertEqual(live.all()[0]['title'], 'Later change')

    def test_existing_destination_and_non_database_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            seed(root / 'source.db')
            target = root / 'precious.db'
            target.write_bytes(b'keep me')
            with self.assertRaises(FileExistsError):
                copy_database(root / 'source.db', target)
            self.assertEqual(target.read_bytes(), b'keep me')
            Store(root / 'empty.db')
            import sqlite3
            invalid = root / 'unrelated.db'
            with closing(sqlite3.connect(invalid)) as db:
                db.execute('CREATE TABLE unrelated (id INTEGER)')
            with self.assertRaises(ValueError):
                copy_database(invalid, root / 'failed.db')
            self.assertFalse((root / 'failed.db').exists())

    def test_demo_refuses_to_modify_existing_work(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'demo.db'
            item = seed(path)
            with self.assertRaises(ValueError):
                seed(path)
            self.assertEqual(Store(path).all(), [item])


if __name__ == '__main__':
    unittest.main()
