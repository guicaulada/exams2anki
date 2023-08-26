# exams2anki

Convert [ExamTopics](https://www.examtopics.com/exams/) pages to Anki decks!

## Requirements

At least one of the following webdrivers must be installed and in your PATH environment variable:
- [chromedriver](https://chromedriver.chromium.org/)
- [Edge WebDriver](https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/)

Chrome will be used by default, if you wish to use the Edge WebDriver use the flag `--edge`.

## Installation

- `pip install exams2anki`

## Usage

- `exams2anki --help`

## Install local version

If you have cloned this repository you can run:

```
python3 setup.py install
```

## Build and publish

If you had created this package you would be able to run:

```
python3 setup.py sdist bdist_wheel
twine upload dist/*
```

## Template

You can experiment creating your own template based on the existing ones using the `--template` option.

## License

```
exams2anki - Convert ExamTopics pages to Anki decks
Copyright (C) 2021  Guilherme Caulada

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
```
