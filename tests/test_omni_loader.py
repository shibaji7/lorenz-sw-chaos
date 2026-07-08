from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from lorenzsw.forcing.omni_loader import load_omni_index


@dataclass
class _Response:
    text: str
    status_code: int = 200

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class _Session:
    def __init__(self, post_text: str, get_text: str):
        self._post_text = post_text
        self._get_text = get_text
        self.post_calls: list[tuple[str, dict[str, str]]] = []
        self.get_calls: list[str] = []

    def __enter__(self) -> "_Session":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def post(self, url: str, data: dict[str, str], timeout: float) -> _Response:
        self.post_calls.append((url, data))
        return _Response(self._post_text)

    def get(self, url: str, timeout: float) -> _Response:
        self.get_calls.append(url)
        return _Response(self._get_text)


def test_load_omni_index_parses_staging_response_and_caches(tmp_path, monkeypatch):
    staging_text = "OMNI staging file: https://omniweb.gsfc.nasa.gov/staging/omni2_demo.lst"
    data_text = "\n".join(
        [
            "YEAR DOY HR MN SEC SYM_H",
            "2020 001 00 00 00 10.0",
            "2020 001 01 00 00 11.0",
        ]
    )
    session = _Session(staging_text, data_text)
    monkeypatch.setattr(
        "lorenzsw.forcing.omni_loader.requests.Session",
        lambda: session,
    )

    frame = load_omni_index("2020-01-01", "2020-01-02", index="SYM_H", cache_dir=str(tmp_path))

    assert isinstance(frame, pd.DataFrame)
    assert list(frame.columns) == ["SYM_H"]
    assert len(frame) == 2
    assert str(frame.index.tz) == "UTC"
    assert frame.iloc[0, 0] == 10.0
    assert len(session.post_calls) == 1
    assert len(session.get_calls) == 1

    cached = load_omni_index("2020-01-01", "2020-01-02", index="SYM_H", cache_dir=str(tmp_path))
    pd.testing.assert_frame_equal(frame, cached)
