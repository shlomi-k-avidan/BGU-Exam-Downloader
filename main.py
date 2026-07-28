#!/usr/bin/env python3
"""
BGU Scanned-Exam Downloader (legacy student project, cleaned up for publication).

Logs into Ben-Gurion University's "Gezer" exam system with the student's own
credentials, lists the year's graded/scanned exams, and downloads the scanned
exam PDFs — individually, in batch, or by fully manual course details.

Historical note: when this was written, scanned PDFs were retrievable via a
reconstructed download token before the official grade-publication date (the
release gate existed only in the UI; the endpoint performed no authorization
check on publication state). That behavior has since been fixed by the
university. This tool only ever accessed the logged-in student's own documents.
"""

from __future__ import annotations

import base64
import getpass
import os
import subprocess
import sys
import threading
import time
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SITE = "https://gezer1.bgu.ac.il/meser/"
LOGIN_PAGE = "login.php"
MAIN_PAGE = "main.php"
PRE_DOWNLOAD_PAGE = "tiflink.php"
DOWNLOAD_PAGE = "exam.php"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.41"
)
REQUEST_TIMEOUT = 100  # seconds
MAX_LOGIN_ATTEMPTS = 3

TOKEN_TEMPLATE = "{student_id}:{year}:{semester}:0:{bohan_param}:{course_id}:1:{moed}"
FILE_TEMPLATE = "{student_id}_{course_id}_{moed}.pdf"
SCANNED_STATUS_MARKER = "appear after grades"

MOED_CHOICES = ("1", "2", "3", "4", "11")  # 11 = quiz (bohan)
SEMESTER_CHOICES = ("1", "2", "3")         # 1 = fall, 2 = spring, 3 = summer

BANNER = r"""
        ############################################################
        #           BGU SCANNED-EXAM DOWNLOADER (legacy)           #
        #     Downloads *your own* scanned exams from Gezer.       #
        ############################################################
"""


# ---------------------------------------------------------------------------
# Console helpers (ANSI colors)
# ---------------------------------------------------------------------------

class C:
    RED = "\033[1;31m"
    GREEN = "\033[1;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[1;34m"
    MAGENTA = "\033[1;35m"
    CYAN = "\033[1;36m"
    WHITE = "\033[1;37m"
    DEFAULT = "\033[1;39m"
    RESET = "\033[0m"


MOED_COLORS = {"A": C.YELLOW, "B": C.MAGENTA, "C": C.WHITE, "D": C.WHITE, "QUIZ": C.BLUE}
SEMESTER_COLORS = {"A": C.BLUE, "B": C.CYAN, "C": C.GREEN}


def info(msg: str) -> None:
    print(f"{C.CYAN}[*]{C.RESET} {msg}")


def ok(msg: str) -> None:
    print(f"{C.GREEN}[+]{C.RESET} {msg}")


def err(msg: str) -> None:
    print(f"{C.RED}[X]{C.RESET} {msg}")


def ask(msg: str) -> str:
    return input(f"{C.YELLOW}[#] {msg}{C.RESET}\n    {C.YELLOW}>>> {C.RESET}").strip()


def grade_color(grade: str) -> str:
    """Color-code a grade: red <56, green 56-89, blue 90-99, yellow 100+."""
    try:
        value = int(grade)
    except ValueError:
        return C.DEFAULT
    if value < 56:
        return C.RED
    if value < 90:
        return C.GREEN
    if value < 100:
        return C.BLUE
    return C.YELLOW


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Course:
    name: str
    course_id: str
    moed: int        # 1-4, or 11 for quiz
    semester: int    # 1 = fall, 2 = spring, 3 = summer
    year: str
    exam_grade: str = "XXX"
    final_grade: str = "XXX"
    unpublished: bool = False

    @property
    def moed_label(self) -> str:
        return "QUIZ" if self.moed == 11 else chr(ord("A") + self.moed - 1)

    @property
    def semester_label(self) -> str:
        return chr(ord("A") + self.semester - 1)

    def describe(self, index: int | None = None) -> str:
        moed = MOED_COLORS.get(self.moed_label, C.DEFAULT)
        sem = SEMESTER_COLORS.get(self.semester_label, C.DEFAULT)
        prefix = f"({index}) " if index is not None else ""
        return (
            f"{prefix}{self.course_id} - {self.name}, "
            f"{moed}Moed {self.moed_label}{C.RESET}, "
            f"{sem}Semester {self.semester_label}{C.RESET} {self.year} | "
            f"{grade_color(self.exam_grade)}Exam Grade: {self.exam_grade}{C.RESET} | "
            f"{grade_color(self.final_grade)}Final Grade: {self.final_grade}{C.RESET}"
        )


# ---------------------------------------------------------------------------
# Page parsing
# ---------------------------------------------------------------------------

def _map_semester(text: str, previous: int = 0) -> int:
    if "fall" in text:
        return 1
    if "spring" in text:
        return 2
    if "summer" in text:
        return 3
    if "irregular" in text:
        return previous
    return 0


def _map_moed(text: str) -> int:
    if "first" in text:
        return 1
    if "second" in text:
        return 2
    if "special" in text:
        return 3
    if "quiz" in text:
        return 11
    return 0


def _grade_from(cell: str) -> str:
    grade = cell[-2:]
    try:
        assert 0 <= int(grade) <= 150
        return grade
    except (ValueError, AssertionError):
        return "XXX"


def parse_courses(html: str) -> list[Course]:
    """Extract exam rows from the Gezer course-table HTML."""
    soup = BeautifulSoup(html, "html.parser")
    courses: list[Course] = []
    for row in soup.find_all("tr"):
        cells = [
            td.get_text(" ", strip=True).replace("\xa0", " ").strip()
            for td in row.find_all("td")
            if td.find("input") is None
        ]
        cells = [c for c in cells if len(c) >= 5]
        if len(cells) < 6:
            continue

        unpublished = SCANNED_STATUS_MARKER in cells[5].lower()
        has_final_grade = len(cells) == 7 and cells[6][-1:].isdigit()
        looks_like_exam_row = len(cells) == 6 and cells[4][-1:].isdigit()
        if not (unpublished or has_final_grade or looks_like_exam_row):
            continue

        year = cells[4][-4:].strip()
        if not year.isnumeric():
            year = ""

        course = Course(
            name=cells[1].strip(),
            course_id=cells[0].strip(),
            moed=_map_moed(cells[3].lower()),
            semester=_map_semester(cells[2].lower(), previous=courses[-1].semester if courses else 0),
            year=year,
            unpublished=unpublished,
        )
        course.exam_grade = _grade_from(cells[5])
        if len(cells) == 7:
            course.final_grade = _grade_from(cells[6])
        courses.append(course)
    return courses


# ---------------------------------------------------------------------------
# Gezer session
# ---------------------------------------------------------------------------

def _prompt_credentials() -> tuple[str, str, str]:
    username = ""
    while not username:
        username = ask("BGU username:")
    password = getpass.getpass("    BGU password (input hidden): ")
    student_id = ""
    while not (len(student_id) == 9 and student_id.isdigit()):
        student_id = ask("Israeli ID number (9 digits):")
    return username, password, student_id


def login(session: requests.Session) -> tuple[requests.Response, str] | tuple[None, None]:
    """Log into Gezer. Returns (course-page response, student_id) or (None, None)."""
    for attempt in range(1, MAX_LOGIN_ATTEMPTS + 1):
        username, password, student_id = _prompt_credentials()
        info("Logging into Gezer system...")
        try:
            session.get(SITE + LOGIN_PAGE, headers={"Referer": SITE + PRE_DOWNLOAD_PAGE},
                        timeout=REQUEST_TIMEOUT)
            response = session.post(
                SITE + MAIN_PAGE,
                data={"username": username, "pass": password, "id": student_id,
                      "ok": "Next", "isheb": 0},
                timeout=REQUEST_TIMEOUT,
            )
        except requests.RequestException as exc:
            err(f"Login request failed ({exc}). Retrying...")
            continue

        if "entrance" in response.text.lower():
            err(f"Login failed (attempt {attempt}/{MAX_LOGIN_ATTEMPTS}).")
            continue

        ok("Logged in to Gezer system successfully!")
        return response, student_id

    err("Too many failed login attempts, exiting.")
    return None, None


def build_token(course: Course, student_id: str) -> str:
    """Reconstruct the base64 download token for an exam."""
    bohan_param = course.semester * (course.moed not in (3, 4, 11)) + 4 * (course.moed in (3, 4, 11))
    raw = TOKEN_TEMPLATE.format(
        student_id=student_id,
        year=course.year,
        semester=course.semester,
        bohan_param=bohan_param,
        course_id=course.course_id,
        moed=course.moed,
    )
    return base64.b64encode(raw.encode("utf-8")).decode("utf-8")


def _open_file(path: str) -> None:
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except OSError:
        info(f"Could not auto-open the file; open it manually: {path}")


def download_exam(session: requests.Session, course: Course, student_id: str) -> None:
    """Download a single exam PDF (runs inside worker threads)."""
    filename = FILE_TEMPLATE.format(
        student_id=student_id, course_id=course.course_id, moed=course.moed
    )
    info(f"Downloading {filename} ...")
    try:
        response = session.post(
            SITE + DOWNLOAD_PAGE,
            data={"toopen:2:1": "Download as PDF", "expars": build_token(course, student_id)},
            headers={"Referer": SITE + PRE_DOWNLOAD_PAGE,
                     "Content-Type": "application/x-www-form-urlencoded"},
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        err(f"Download request failed for course {course.course_id}: {exc}")
        return

    if "firewall" in response.text or "cant open" in response.text:
        err(f"Exam not found in the database: {course.describe()}")
        return
    if "No connection to database" in response.text:
        err("The exam database is currently offline. Please try again later.")
        return

    try:
        with open(filename, "wb") as handle:
            handle.write(response.content)
    except OSError as exc:
        err(f"Failed to write {filename} to disk: {exc}")
        return

    ok(f"Downloaded {filename}")
    _open_file(filename)


def download_async(session: requests.Session, course: Course, student_id: str,
                   threads: list[threading.Thread]) -> None:
    thread = threading.Thread(target=download_exam, args=(session, course, student_id))
    thread.start()
    threads.append(thread)
    time.sleep(1)  # gentle pacing; keeps console output readable


# ---------------------------------------------------------------------------
# Interactive flow
# ---------------------------------------------------------------------------

def prompt_manual_course() -> Course:
    course_id = ""
    while not (len(course_id) == 8 and course_id.isdigit()):
        course_id = ask("Course ID (e.g. 20119631):")
    moed = ""
    while moed not in MOED_CHOICES:
        moed = ask("Moed (1/2/3/4, or 11 for quiz):")
    semester = ""
    while semester not in SEMESTER_CHOICES:
        semester = ask("Semester (1 = fall / 2 = spring / 3 = summer):")
    year = ""
    while not (len(year) == 4 and year.isdigit()):
        year = ask("Exam year (e.g. 2023):")
    return Course(name="(manual entry)", course_id=course_id,
                  moed=int(moed), semester=int(semester), year=year)


def main() -> int:
    print(C.YELLOW + BANNER + C.RESET)

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    response, student_id = login(session)
    if response is None:
        return 1

    courses = parse_courses(response.content.decode("ISO-8859-1", errors="replace"))
    threads: list[threading.Thread] = []

    unpublished = [c for c in courses if c.unpublished]
    if unpublished:
        info("Newly scanned (not yet published) exams detected:")
        for course in unpublished:
            print("    " + course.describe())
        if ask("Download all of them now? [Y/N]").lower() == "y":
            for course in unpublished:
                download_async(session, course, student_id, threads)

    info("Enter a number to download one exam, '*' for all, '$' for manual entry, 'q' to quit.")
    try:
        while True:
            if courses:
                print()
                for i, course in enumerate(courses, start=1):
                    print("    " + course.describe(index=i))
                choice = ask(f"Exam to download [1-{len(courses)} / * / $ / q]:")
            else:
                info("No exams listed for this year; manual mode.")
                choice = "$"

            if choice.lower() == "q":
                break
            if choice == "$":
                download_async(session, prompt_manual_course(), student_id, threads)
            elif choice == "*":
                for course in courses:
                    download_async(session, course, student_id, threads)
                info("All downloads tasked in the background.")
            else:
                try:
                    index = int(choice) - 1
                    assert 0 <= index < len(courses)
                except (ValueError, AssertionError):
                    err("Invalid choice.")
                    continue
                download_async(session, courses[index], student_id, threads)
    except (KeyboardInterrupt, EOFError):
        print()

    if threads:
        info("Waiting for background downloads to finish...")
        for thread in threads:
            thread.join()
    ok("Done. Good luck on your exams!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
