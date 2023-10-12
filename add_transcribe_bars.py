from bar_analysis import AudioData
from transcribe_reader import TranscribeData, TranscribeLine
from pathlib import Path


def make_transcribe_bar_markers(data: AudioData) -> list[TranscribeLine]:
    bar_markers = data.get_bars()
    return [TranscribeLine("HowMany", [f"{len(bar_markers)}"])] + [
        (
            TranscribeLine.measure_line(
                bar.timestamp.to_float(), str(bar.bar_number + 1), bar.num_beats, True
            )
        )
        for bar in bar_markers
    ]


def calculate_bar_markers(
    path: str | Path, output_path: None | str | Path = None
) -> None:
    if isinstance(path, str):
        path = Path(path)
    if output_path is None:
        output_path = path
    elif isinstance(output_path, str):
        output_path = Path(output_path)
    print("Reading Transcribe file")
    transcribe = TranscribeData.from_file(path)
    soundfile = transcribe.get_soundfile_path()
    print(f"Reading sound file from {soundfile}")
    audio = AudioData.from_file(soundfile)
    print("Calculating tempo")
    mean_temp = audio.mean_tempo
    print(f"Mean tempo is {mean_temp:.2f} bpm")
    print("Calculating bar markers")
    marker_section = make_transcribe_bar_markers(audio)
    print(f"Writing new bar markers to {output_path}")
    transcribe.replace_section("Markers", marker_section)
    with output_path.open(mode="w") as handle:
        print("\n".join(transcribe.write()), file=handle)


def main():
    import sys

    if len(sys.argv) < 2 or len(sys.argv) > 3:
        path = Path(sys.argv[0])
        print(f"{path.name} INPUT_FILE [OUTPUT_FILE]")
        sys.exit(1)
    calculate_bar_markers(sys.argv[1], sys.argv[2] if len(sys.argv) == 3 else None)


if __name__ == "__main__":
    main()
