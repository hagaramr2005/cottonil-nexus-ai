import sqlite3
import pytest
from pathlib import Path
from scripts.db_ops import backup,restore


def test_backup_restore_guard(tmp_path):
    original=tmp_path/'sample.sqlite';copy=tmp_path/'copy.sqlite';restored=tmp_path/'restored.sqlite'
    with sqlite3.connect(original) as c:
        c.execute('CREATE TABLE demo(id INTEGER PRIMARY KEY, name TEXT)')
        c.execute("INSERT INTO demo VALUES (1,'SYNTHETIC')")
    digest=backup(original,copy)
    assert len(digest)==64
    with pytest.raises(RuntimeError,match='--force'):restore(copy,restored)
    assert restore(copy,restored,force=True)==digest
    with sqlite3.connect(restored) as c:
        assert c.execute('SELECT name FROM demo').fetchone()[0]=='SYNTHETIC'
    with pytest.raises(FileExistsError):restore(copy,restored,force=True)
