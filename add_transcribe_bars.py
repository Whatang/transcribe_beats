from bar_analysis import AudioData
from transcribe_reader import TranscribeData, TranscribeLine
from pathlib import Path


def make_transcribe_bar_markers(data: AudioData) -> list[TranscribeLine]:
    bar_markers = data.get_bars()
    return [TranscribeLine("HowMany", [f"{len(bar_markers)}"])] + [
        (
            TranscribeLine.measure_line(
                bar.timestamp.to_float(), str(bar.bar_number + 1), bar.num_beats, False
            )
        )
        for bar in bar_markers
    ]


def calculate_bar_markers(path: str | Path) -> None:
    transcribe = TranscribeData.from_file(path)
    soundfile = transcribe.get_soundfile_path()
    audio = AudioData.from_file(soundfile)
    marker_section = make_transcribe_bar_markers(audio)
    transcribe.replace_section("Markers", marker_section)
    with path.open(mode="w") as handle:
        print("\n".join(transcribe.write()), file=handle)
