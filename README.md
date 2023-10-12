# Automatic bar marker generation for Transcribe!

[Transcribe!](https://www.seventhstring.com/) is a commercial music player specifically intended to aid in music transcription. It has the facility to add beat, measure, and section markers, which is extremely useful when transcribing. However, you have to add these manually which I find very tedious. This repository contains code to automatically create measure markers using the beat analysis in the [QM Vamp Plugin](https://vamp-plugins.org/plugin-doc/qm-vamp-plugins.html).

## Dependencies

* `numpy` - used by the Vamp plugins.
* `librosa` - an audio file processing Python library.
* [`vamp`](https://code.soundsoftware.ac.uk/projects/vampy-host/repository) (or on [PyPi](https://pypi.org/project/vamp/)) - a Python host for Vamp plugins. Might need to be compiled, since pre-compiled wheels are not available for Windows and Python 3.
* The [QM Vamp Plugins](https://vamp-plugins.org/plugin-doc/qm-vamp-plugins.html#qm-tempotracker) - used to detect the tempo, beats, and bars in the soundfile.

## Files

* `transcribe_reader.py` contains classes for interacting the the Transcribe .xsc file format.
* `bar_analysis.py` uses the QM Vamp plugin to determine the location of bar markers in a sound file.
* `add_transcribe_bars.py` uses the above two modules to read a Transcribe .xsc file; analyse the bar locations in the sound file it references; then write the measure markers back to the .xsc file. This file can be run on the command line to modify Transcribe files directly.

There are also two Jupyter notebooks which demonstrate how the analysis works and how the parts all fit together:

* `vamp_plugin_experiment.ipynb` demonstrates experimenting with the QM Vamp plugins to detect tempo and bar markers, then understanding how to turn this into data that Transcribe understands. This was how I worked out what to do, and this understanding was used as the basis for the Python files above.
* `analysis.ipynb` shows how the various functions and classes implemented in the above Python files work together to analyse an audio file and create measure markers in the corresponding Transcribe file.