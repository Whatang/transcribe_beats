from __future__ import annotations
from typing import Iterable
from dataclasses import dataclass
from pathlib import Path
import itertools


def _unquote_transcribe(s: str) -> str:
    output = ""
    escaping = False
    for c in s:
        if escaping:
            if c == "\\":
                output += c
            elif c in ("n", "r", "t"):
                output += ("\\" + c).encode("utf-8").decode("unicode_escape")
            elif c == "C":
                output += ","
            else:
                raise ValueError("Do not know how to parse this escape character", c)
            escaping = False
        elif c == "\\":
            escaping = True
        else:
            output += c
    if escaping:
        output += "\\"
    return output


def _quote_transcribe(s: str) -> str:
    s = s.replace("\\", "\\\\").replace(",", "\\C")
    s = s.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
    return s


def to_transcribe_time(v: float) -> str:
    return (
        f"{int(v//3600):01d}:{int(v//60) % 60:02d}:{int(v)%60:02d}."
        + f"{v:.6f}".split(".")[1]
    )


@dataclass
class TranscribeLine:
    line_type: str
    fields: list[str]

    @classmethod
    def parse(cls, line_data: str) -> TranscribeLine:
        lt, data = line_data.split(",", 1)
        data = [_unquote_transcribe(d) for d in data.split(",")]
        return TranscribeLine(lt, data)

    def write(self) -> str:
        return ",".join([self.line_type] + [_quote_transcribe(f) for f in self.fields])

    @classmethod
    def measure_line(
        cls, timestamp: float, label: str, subdivision: int, autogen: bool = False
    ) -> TranscribeLine:
        return TranscribeLine(
            "M",
            [
                "-1",
                "1" if autogen else "0",
                label,
                str(subdivision),
                to_transcribe_time(timestamp),
            ],
        )


TRANSCRIBE_SECTION = list[TranscribeLine]
TRANSCRIBE_SECTION_MAP = dict[str, TRANSCRIBE_SECTION]


@dataclass
class TranscribeData:
    @dataclass
    class Header:
        format_version: str
        transcribe_version: str
        format_line: str
        tv_line: str

        @classmethod
        def parse(cls, lines: Iterable[str]) -> TranscribeData.Header:
            line_iterator = iter(line.strip() for line in lines if line.strip())
            first_line = next(line_iterator)
            if not first_line.startswith("XSC Transcribe.Document Version"):
                raise ValueError("Cannot determine XSC format number")
            xsc_format = first_line.rsplit(" ", 1)[-1]
            second_line = next(line_iterator)
            parsed_second_line = TranscribeLine.parse(second_line)
            if parsed_second_line.line_type != "Transcribe!":
                raise ValueError("Cannot determine Transcribe version")
            transcribe_version = (
                parsed_second_line.fields[0]
                + " "
                + ".".join(parsed_second_line.fields[1:])
            )
            return cls(
                format_version=xsc_format,
                transcribe_version=transcribe_version,
                format_line=first_line,
                tv_line=second_line,
            )

    header: Header
    sections: TRANSCRIBE_SECTION_MAP

    @classmethod
    def from_file(cls, path: str | Path) -> TranscribeData:
        if isinstance(path, str):
            path = Path(path)
        line_data = path.read_text().splitlines()
        header, sections = cls._parse_lines(line_data)
        return cls(header, sections)

    @staticmethod
    def _parse_lines(lines: Iterable[str]) -> (Header, TRANSCRIBE_SECTION_MAP):
        header = TranscribeData.Header.parse(lines)
        # Skip the first two non-empty lines, they're the header
        line_iterator = map(
            TranscribeLine.parse,
            itertools.islice(
                iter(line.strip() for line in lines if line.strip()), 2, None
            ),
        )
        current_section: str | None = None
        section_lines: TRANSCRIBE_SECTION = []
        sections: TRANSCRIBE_SECTION_MAP = {}
        for line in line_iterator:
            if current_section is None:
                if line.line_type == "SectionStart":
                    current_section = line.fields[0]
                    if current_section in sections:
                        raise ValueError(
                            "Parse error: section appears twice", current_section
                        )
                else:
                    raise ValueError("Parse error: non-header data outside a section")
            elif line.line_type == "SectionEnd":
                if line.fields[0] != current_section:
                    raise ValueError(
                        "Parse error: section end for mismatching section",
                        current_section,
                        line.fields[0],
                    )
                else:
                    sections[current_section] = section_lines
                    section_lines = []
                    current_section = None
            else:
                section_lines.append(line)
        if current_section is not None:
            raise ValueError(
                "Parse error: section incomplete before file end", current_section
            )
        return header, sections

    def get_soundfile_path(self) -> Path:
        main_section = self.sections["Main"]
        for line in main_section:
            if line.line_type == "SoundFileName":
                return Path(line.fields[-1])
        raise ValueError("Could not find sound file path in Transcribe data")

    def replace_section(self, section_name: str, new_data: TRANSCRIBE_SECTION) -> None:
        self.sections[section_name] = list(new_data)

    def write(self) -> list[str]:
        output = [self.header.format_line, self.header.tv_line]
        for section_title, section_data in self.sections.items():
            output.append("")
            output.append(f"SectionStart,{section_title}")
            output.extend(line.write() for line in section_data)
            output.append(f"SectionEnd,{section_title}")
        output.append("")
        return output
