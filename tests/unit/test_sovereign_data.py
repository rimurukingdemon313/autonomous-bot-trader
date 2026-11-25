"""The owner's SOVEREIGN package is kept as received, and its fetcher (scripts/sovereign_data.py) stores what is
served and names what is not."""

import hashlib
import importlib.util
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from scripts import sovereign_data as sd
from tests.unit.test_trinity_data import _res

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "external" / "sovereign"
NOW = datetime(2026, 11, 24, 23, 0, tzinfo=timezone.utc)


def test_the_package_is_the_spec_s_own_code_byte_for_byte():
    spec = (PKG / "Claude_Handoff_Top3_Strategies.md").read_text()
    blocks = re.findall(r"```python\n(.*?)```", spec, flags=re.S)
    assert len(blocks) == 1
    assert (PKG / "sovereign_top3_suite.py").read_text() == blocks[0]
    readme = (PKG / "README.md").read_text()
    for f in ("Claude_Handoff_Top3_Strategies.md", "sovereign_top3_suite.py"):
        assert hashlib.sha256((PKG / f).read_bytes()).hexdigest() in readme, f


def test_the_fetcher_asks_for_exactly_the_package_s_seven_funds():
    spec = importlib.util.spec_from_file_location("sovereign_pkg", PKG / "sovereign_top3_suite.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    assert set(sd.SYMBOLS) == set(m.SECTORS) and len(sd.SYMBOLS) == 7


def test_write_stores_what_is_served_and_names_what_is_not(tmp_path):
    good = _res([(datetime(2026, 11, 20, 14, 30, tzinfo=timezone.utc), 10, 11, 9, 10.5, 100, 10.4),
                 (datetime(2026, 11, 23, 14, 30, tzinfo=timezone.utc), 10.5, 12, 10, 11.0, 50, 10.9)])
    empty = _res([])

    def fetch(sym, first, now):
        if sym == "SLV":
            raise OSError("host refused")
        return empty if sym == "IBIT" else good

    man = sd.write(tmp_path, NOW, fetch=fetch)
    assert set(man["failed"]) == {"SLV", "IBIT"}
    assert not (tmp_path / "history" / "SLV.json").exists() and not (tmp_path / "history" / "IBIT.json").exists()
    rows = json.loads((tmp_path / "history" / "QQQ.json").read_text())
    assert rows == {"2026-11-20": {"o": 10.0, "h": 11.0, "l": 9.0, "c": 10.5, "v": 100.0, "adj": 10.4},
                    "2026-11-23": {"o": 10.5, "h": 12.0, "l": 10.0, "c": 11.0, "v": 50.0, "adj": 10.9}}
    s = man["series"]["QQQ"]
    assert (s["rows"], s["first"], s["last"]) == (2, "2026-11-20", "2026-11-23")
    assert s["sha256"] == hashlib.sha256((tmp_path / "history" / "QQQ.json").read_bytes()).hexdigest()
    assert json.loads((tmp_path / "history" / "manifest.json").read_text())["failed"] == man["failed"]


def test_the_extra_set_writes_safe_names_in_its_own_folder(tmp_path):
    good = _res([(datetime(2026, 11, 20, 14, 30, tzinfo=timezone.utc), 10, 11, 9, 10.5, 100, 10.4)])
    man = sd.write(tmp_path, NOW, fetch=lambda sym, first, now: good, symbols=sd.EXTRA, folder="history_extra")
    assert not man["failed"] and set(man["series"]) == set(sd.EXTRA)
    assert (tmp_path / "history_extra" / "_GDAXI.json").exists() and (tmp_path / "history_extra" / "BTC-USD.json").exists()
    assert man["series"]["^N225"]["file"] == "history_extra/_N225.json"
    assert not (tmp_path / "history").exists()
    assert [sd.file_name(s) for s in sd.SYMBOLS] == list(sd.SYMBOLS)  # the core files keep their names
