# BGU Scanned-Exam Downloader (legacy student-era project)

A small Windows utility I wrote during my B.Sc. at Ben-Gurion University (2023) to save myself and my classmates the daily ritual of checking the university's exam system ("Gezer") for newly scanned exams. It logs in with the student's own BGU credentials, lists the year's graded/scanned exams with grades color-coded in the terminal, and downloads the scanned exam PDFs automatically as they appear — including a batch mode (`*` = download everything) and background, threaded downloads that open each PDF when ready.

> **Status: historical.** The underlying system behavior described below was since fixed by the university, and the tool is kept here as a record of early work, not as a maintained project.

## The interesting part (why this exists)

The exam system displayed scanned exams with a status of *"available after grade publication."* In practice, the scanned PDF was already sitting on the server — access was gated only by the UI, and the download endpoint accepted a simple base64 token of the form:

```
<student-id>:<year>:<semester>:0:<bohan-param>:<course-id>:1:<moed>
```

Reconstructing that token retrieved your **own** scanned exam as soon as it was uploaded, days before the official grade publication. No other student's data was ever accessible — the token is built from the logged-in student's own ID and only ever requested that student's own documents. This tool automated the reconstruction so the exam appeared the moment the scanner finished, not the moment the registrar allowed it.

The university has since fixed this behavior. It was a good first lesson in the question that starts most real security work: *the UI says unavailable — but is it actually unavailable?*

## Usage (historical, Windows)

1. Install Python 3.
2. Run the program (originally via the bundled `.bat` launcher): `python main.py`
3. Log in with your BGU credentials.
4. Pick exams from the detected list, `*` for all, or `$` for fully manual entry.

## Things I would not do today

Keeping the code as it was written is deliberate — it documents where I started:

- **Optional credential storage in base64** (with an in-program warning, at least). Base64 is encoding, not encryption. Today: OS keychain or don't store at all.
- **Bare `except:` blocks everywhere**, global mutable state, and a dependency-check that tries to `pip install` standard-library modules (`time`, `base64`).
- The tool is Windows-only, shells out to Firefox to open PDFs, and parses HTML with string replacement rather than a parser. It worked, it was used, and I've learned a lot since.

## Disclaimer

This tool only ever accessed the logged-in student's own exams through the student's own credentials. It was never intended to access anyone else's data, and it is not for sale — if anyone charged you money for it, you were scammed.
