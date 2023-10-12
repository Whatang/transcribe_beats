from __future__ import annotations

import itertools
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any

import librosa
import numpy as np
import vamp

QM_BEAT_TRACKER = "qm-vamp-plugins:qm-barbeattracker"
QM_TEMPO_TRACKER = "qm-vamp-plugins:qm-tempotracker"
QM_SECTION_DETECT = "qm-vamp-plugins:qm-segmenter"


@dataclass
class AudioData:
    data: np.array
    rate: int
    duration: float
    channels: int
    n_samples: int

    @dataclass
    class BarMarker:
        bar_number: int
        timestamp: Any  # Actually vampyhost.RealTime
        num_beats: int

        def to_transcribe_time(self) -> str:
            v = self.timestamp.values()
            return f"{v[0]//3600:01d}:{v[0]//60:02d}:{v[0]%60:02d}.{v[1]//1000}"

    @dataclass
    class SectionMarker:
        label: str
        timestamp: Any  # Actually vampyhost.RealTime

    @classmethod
    def from_file(cls, path: Path) -> AudioData:
        duration = librosa.get_duration(path=path)

        data, rate = librosa.load(path, sr=None, mono=False)
        if data.ndim == 1:
            channels = 1
            n_samples = len(data)
        else:
            channels, n_samples = data.shape

        return AudioData(data, rate, duration, channels, n_samples)

    @cached_property
    def mean_tempo(self) -> float:
        tempos = vamp.collect(self.data, self.rate * 2, QM_TEMPO_TRACKER)["list"]
        tempo_vals = [float(x["label"].rstrip(" bpm")) for x in tempos if x["label"]]
        if tempo_vals:
            return sum(tempo_vals) / len(tempo_vals)
        return 0.0

    def get_bars(self) -> list[AudioData.BarMarker]:
        bars_and_beats = vamp.collect(
            self.data,
            self.rate,
            QM_BEAT_TRACKER,
            parameters={"inputtempo": self.mean_tempo, "constraintempo": 1},
        )["list"]
        bar_positions = [
            (i, x["timestamp"])
            for i, x in enumerate(bars_and_beats)
            if x["label"] == "1"
        ]
        return [
            AudioData.BarMarker(i, this_pos[1], next_pos[0] - this_pos[0])
            for (i, (this_pos, next_pos)) in enumerate(
                itertools.pairwise(
                    itertools.chain(bar_positions, [(len(bars_and_beats), None)])
                )
            )
        ]

    def get_sections(self) -> list[AudioData.SectionMarker]:
        sections = vamp.collect(self.data, self.rate, QM_SECTION_DETECT)["list"]
        return [
            AudioData.SectionMarker(timestamp=x["timestamp"], label=x["label"])
            for x in sections
        ]

    def get_section_bar_markers(self) -> list[int]:
        bars = iter(self.get_bars())
        sections = iter(self.get_sections())
        indexes = []
        try:
            next_section = next(sections)
            for bar in bars:
                if bar.timestamp > next_section.timestamp:
                    indexes.append(bar.bar_number)
                    next_section = next(sections)
        except StopIteration:
            pass
        return indexes
