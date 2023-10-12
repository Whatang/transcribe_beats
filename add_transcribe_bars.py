import sys
from audio_analysis import AudioData
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


def convert_transcribe_markers_to_sections(
    bar_markers: list[TranscribeLine], section_indexes: list[int]
) -> None:
    for section_bar_index in section_indexes:
        bar = bar_markers[section_bar_index + 1]
        assert bar.fields[2] == str(section_bar_index + 1)
        bar.line_type = "S"


def calculate_bar_markers(
    path: str | Path, output_path: None | str | Path = None, do_sections=False
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
    if do_sections:
        print("Calculating sections")
        section_indexes = audio.get_section_bar_markers()
        convert_transcribe_markers_to_sections(marker_section, section_indexes)
    print(f"Writing new bar markers to {output_path}")
    transcribe.replace_section("Markers", marker_section)
    with output_path.open(mode="w") as handle:
        print("\n".join(transcribe.write()), file=handle)


def usage():
    path = Path(sys.argv[0])
    print(f"{path.name} [-s] INPUT_FILE [OUTPUT_FILE]")
    sys.exit(1)


def main():
    args = sys.argv[1:]
    if not args:
        usage()
    do_sections = args[0] == "-s"
    if do_sections:
        args = args[1:]
    if not args or len(args) > 2:
        usage()
    if len(args) == 1:
        args.append(None)
    calculate_bar_markers(args[0], args[1], do_sections=do_sections)


if __name__ == "__main__":
    main()
