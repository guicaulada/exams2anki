# exams2anki

Convert [ExamTopics](https://www.examtopics.com/exams/) pages to Anki decks!

## Requirements

- You can install all required packages with `pip install -r requirements.txt`
- [chromedriver](https://chromedriver.chromium.org/) must be installed and available on your PATH environment variable

## Usage

```
Usage: exams2anki.py <provider> <exam> <username> <password>
Example: exams2anki.py amazon aws-certified-cloud-practitioner username password
You can also set username and password as environment variables EXAM_TOPICS_EMAIL and EXAM_TOPICS_PASSWORD
To get exam details look for the url on examtopics.com/exams - you MUST have Contributor Access to the exam!
```

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
