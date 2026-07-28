# BGU Scanned-Exam Downloader (legacy student-era project)

A small Windows utility I wrote during my B.Sc. at Ben-Gurion University to save myself and my classmates the daily ritual of checking the university's exam system ("Gezer") for newly scanned exams. It logs in with the student's own BGU credentials, lists the year's graded/scanned exams with grades color-coded in the terminal, and downloads the scanned exam PDFs automatically as they appear — including a batch mode (`*` = download everything) and background, threaded downloads that open each PDF when ready.

> **Status: historical.** The underlying system behavior described below was since fixed by the university, and the tool is kept here as a record of early work, not as a maintained project.

## The interesting part (why this exists)

The exam system displayed scanned exams with a status of *"available after grade publication."* In practice, the scanned PDF was already sitting on the server — access was gated only by the UI, and the download endpoint accepted a simple base64 token of the form:

```
<student-id>:<year>:<semester>:0:<bohan-param>:<course-id>:1:<moed>
```

Reconstructing that token retrieved your **own** scanned exam as soon as it was uploaded, days before the official grade publication. No other student's data was ever accessible — the token is built from the logged-in student's own ID and only ever requested that student's own documents. This tool automated the reconstruction so the exam appeared the moment the scanner finished, not the moment the registrar allowed it.

The university has since fixed this behavior. It was a good first lesson in the question that starts most real security work: *the UI says unavailable — but is it actually unavailable?*

## Usage (historical, Windows)

1. Install Python 3 and the dependencies: `pip install -r requirements.txt`
2. Run `python main.py`
3. Log in with your BGU credentials.
4. Pick exams from the detected list, `*` for all, or `$` for fully manual entry.

## 2026 cleanup

The code was professionally refactored before publication (type hints, a `Course` data model, BeautifulSoup parsing, `getpass` password input, structured error handling). Two original features were deliberately **removed** rather than modernized, because they shouldn't exist under anyone's name:

- **Optional credential storage in base64** — base64 is encoding, not encryption. The original at least warned the user in-program; the correct answer is OS keychain or don't store at all, so storage is gone entirely.
- **The self-modifying "remember my choice" hack** — the original rewrote its own source file to persist a preference. Cute at the time; unacceptable in hindsight.

The original also carried bare `except:` blocks everywhere, a dependency check that tried to `pip install` standard-library modules (`time`, `base64`), and HTML parsing by string replacement. All fixed. The download-token reconstruction, threaded downloads, and terminal UI are preserved from the original.

The original 2023 code is preserved exactly as written at the git tag [`legacy-2023-original`](../../tree/legacy-2023-original).

## Disclaimer

This tool only ever accessed the logged-in student's own exams through the student's own credentials. It was never intended to access anyone else's data, and it is not for sale — if anyone charged you money for it, you were scammed.
