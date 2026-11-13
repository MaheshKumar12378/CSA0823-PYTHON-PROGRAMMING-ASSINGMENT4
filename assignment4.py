"""
CSA08 - Python Programming - Assignment 4 (CO4)
Student: B. Mahesh Kumar | Register No: 1925260023
Topic: Robust Data Processing with Files, Exceptions, Modules and Packages

Run: python assignment4.py
Uses Python standard library only.
"""
from pathlib import Path
from collections import defaultdict
import tempfile
import os
import re


# ----------------------------- TASK 1 ---------------------------------
def process_mess_file(filename):
    """Read mess bills line-by-line; return report, total, rejected records."""
    report = []
    rejected = []
    total = 0.0
    path = Path(filename)

    try:
        with path.open("r", encoding="utf-8") as file:
            for line_no, line in enumerate(file, start=1):
                if not line.strip():
                    continue
                try:
                    parts = [part.strip() for part in line.rstrip("\n").split(",")]
                    if len(parts) != 3:
                        raise ValueError("expected 3 fields")
                    reg_no, name, amount_text = parts
                    amount = float(amount_text)
                    if amount < 0:
                        raise ValueError("amount cannot be negative")
                    report.append(f"{name} {amount:.2f}")
                    total += amount
                except (ValueError, IndexError) as exc:
                    rejected.append((line_no, line.rstrip("\n"), str(exc)))
    except (FileNotFoundError, PermissionError, UnicodeDecodeError) as exc:
        rejected.append((0, str(path), f"{type(exc).__name__}: {exc}"))

    return report, total, rejected


# ----------------------------- TASK 2 ---------------------------------
def process_attendance_files(folder, output_folder, threshold=75.0):
    """
    Input CSV-like lines: register_number,date,status (P/A).
    Processes every .txt or .csv file once and writes monthly reports.
    """
    folder = Path(folder)
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)
    counts = defaultdict(lambda: {"P": 0, "A": 0})
    errors = []

    for path in sorted(list(folder.glob("*.txt")) + list(folder.glob("*.csv"))):
        try:
            with path.open("r", encoding="utf-8") as file:
                for line_no, line in enumerate(file, start=1):
                    if not line.strip():
                        continue
                    try:
                        parts = [x.strip() for x in line.strip().split(",")]
                        if len(parts) != 3:
                            raise ValueError("expected register,date,status")
                        reg, date, status = parts
                        if not reg or not date or status not in {"P", "A"}:
                            raise ValueError("invalid register/date/status")
                        counts[reg][status] += 1
                    except ValueError as exc:
                        errors.append(f"{path.name},{line_no},{exc},{line.rstrip()}")
        except (FileNotFoundError, PermissionError, UnicodeDecodeError) as exc:
            errors.append(f"{path.name},0,{type(exc).__name__},{exc}")

    summary_lines = ["Register Number,Present,Absent,Percentage"]
    below_lines = ["Register Number,Attendance Percentage"]
    for reg, item in sorted(counts.items()):
        total = item["P"] + item["A"]
        percentage = (item["P"] / total * 100) if total else 0.0
        summary_lines.append(f"{reg},{item['P']},{item['A']},{percentage:.2f}")
        if percentage < threshold:
            below_lines.append(f"{reg},{percentage:.2f}")

    (output_folder / "attendance_summary.csv").write_text(
        "\n".join(summary_lines) + "\n", encoding="utf-8")
    (output_folder / "below_75.csv").write_text(
        "\n".join(below_lines) + "\n", encoding="utf-8")
    (output_folder / "damaged_lines.log").write_text(
        "\n".join(errors) + ("\n" if errors else ""), encoding="utf-8")
    return counts, errors


# ----------------------------- TASK 3 ---------------------------------
class InvalidRecord(Exception):
    """Raised when an attendance record does not follow the required format."""


def parse_attendance_line(line):
    parts = line.strip().split(",")
    if len(parts) != 3:
        raise InvalidRecord(f"expected 3 fields, found {len(parts)}")
    reg, date, status = (part.strip() for part in parts)
    if status not in {"P", "A"}:
        raise InvalidRecord(f"invalid status '{status}'")
    if not reg or not date:
        raise InvalidRecord("register number and date cannot be empty")
    return reg, date, status


def summarise_attendance(path):
    present, absent, errors = 0, 0, []
    try:
        with open(path, "r", encoding="utf-8") as file:
            for line_no, line in enumerate(file, start=1):
                if not line.strip():
                    continue
                try:
                    _, _, status = parse_attendance_line(line)
                    if status == "P":
                        present += 1
                    else:
                        absent += 1
                except InvalidRecord as exc:
                    errors.append((line_no, str(exc)))
    except FileNotFoundError as exc:
        raise RuntimeError(f"attendance file not found: {path}") from exc
    except (PermissionError, UnicodeDecodeError) as exc:
        raise RuntimeError(f"cannot read attendance file: {path}") from exc
    else:
        pass
    finally:
        # The with statement closes the file even if parsing fails.
        pass
    return present, absent, errors


# ----------------------------- TASK 4 ---------------------------------
def save_returns(books, log_path):
    """Append each returned book on a separate line."""
    with open(log_path, "a", encoding="utf-8") as log:
        for book in books:
            book = book.strip()
            if book:
                log.write(book + "\n")


def process_return_day(day_file, log_path, error_log):
    try:
        with open(day_file, "r", encoding="utf-8") as source:
            books = source.read().splitlines()
        save_returns(books, log_path)
    except (FileNotFoundError, PermissionError, UnicodeDecodeError, OSError) as exc:
        with open(error_log, "a", encoding="utf-8") as errors:
            errors.write(f"{day_file}: {type(exc).__name__}: {exc}\n")


# ----------------------------- TASK 5 ---------------------------------
# Organisation (a): one script - functions are kept together in this file.
# Organisation (b): a module imported by a main script:
#   attendance_utils.py contains reader, stats and report functions.
#   main.py uses: import attendance_utils
# Organisation (c): three modules in one folder:
#   attendance_project/reader.py, stats.py, report.py
# Organisation (d): package:
#   attendance/ __init__.py, reader.py, stats.py, report.py
#
# Reusable functions used by all organisations:
def read_records(paths):
    records = []
    errors = []
    for path in paths:
        try:
            with open(path, "r", encoding="utf-8") as file:
                records.extend(line.strip() for line in file if line.strip())
        except (FileNotFoundError, PermissionError, UnicodeDecodeError) as exc:
            errors.append((str(path), type(exc).__name__, str(exc)))
    return records, errors


def attendance_statistics(records):
    result = defaultdict(lambda: {"P": 0, "A": 0})
    for record in records:
        try:
            reg, date, status = parse_attendance_line(record)
            result[reg][status] += 1
        except InvalidRecord:
            continue
    return dict(result)


def write_attendance_report(statistics, destination):
    with open(destination, "w", encoding="utf-8") as file:
        file.write("Register,Present,Absent,Percentage\n")
        for reg, item in sorted(statistics.items()):
            total = item["P"] + item["A"]
            percent = item["P"] / total * 100 if total else 0
            file.write(f"{reg},{item['P']},{item['A']},{percent:.2f}\n")


def consecutive_absentees(daily_records):
    """Return register numbers absent on at least three consecutive dates."""
    by_student = defaultdict(dict)
    for reg, date, status in daily_records:
        by_student[reg][date] = status
    result = []
    for reg, days in by_student.items():
        ordered = sorted(days)
        streak = 0
        previous = None
        for date in ordered:
            if days[date] == "A":
                # The supplied dates are sorted; streak means consecutive records/days.
                streak = streak + 1 if previous is not None else 1
                if streak >= 3:
                    result.append(reg)
                    break
            else:
                streak = 0
            previous = date
    return sorted(set(result))


# ----------------------------- TASK 6 ---------------------------------
def valid_email(email):
    email = email.strip()
    if email.count("@") != 1:
        return False
    local, domain = email.split("@")
    return bool(local and domain and "." in domain and
                not email.startswith("@") and not email.endswith("@") and
                " " not in email)


def process_fest_files(input_folder, output_folder, expected_files=None):
    """
    Registration format:
    register,name,department,email,event1;event2
    Register number is the unique key. First valid registration is retained.
    """
    input_folder, output_folder = Path(input_folder), Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)
    if expected_files is None:
        expected_files = [f"department{i}.csv" for i in range(1, 6)]

    master = {}
    event_map = defaultdict(set)
    errors = []
    for filename in expected_files:
        path = input_folder / filename
        try:
            with path.open("r", encoding="utf-8") as file:
                for line_no, line in enumerate(file, start=1):
                    if not line.strip():
                        continue
                    try:
                        parts = [x.strip() for x in line.rstrip("\n").split(",")]
                        if len(parts) != 5:
                            raise ValueError("expected 5 fields")
                        reg, name, department, email, events_text = parts
                        if not reg or not name or not department:
                            raise ValueError("register, name and department are required")
                        if not valid_email(email):
                            raise ValueError("invalid email address")
                        events = {e.strip() for e in events_text.split(";") if e.strip()}
                        if not events:
                            raise ValueError("at least one event is required")
                        if reg in master:
                            errors.append(f"{filename},{line_no},duplicate registration,{reg}")
                            continue
                        master[reg] = {
                            "name": name, "department": department,
                            "email": email.lower(), "events": sorted(events)
                        }
                        for event in events:
                            event_map[event].add(reg)
                    except ValueError as exc:
                        errors.append(f"{filename},{line_no},{exc},{line.rstrip()}")
        except (FileNotFoundError, PermissionError, UnicodeDecodeError, OSError) as exc:
            errors.append(f"{filename},0,{type(exc).__name__},{exc}")

    with (output_folder / "master_list.csv").open("w", encoding="utf-8") as file:
        file.write("Register,Name,Department,Email,Events\n")
        for reg, item in sorted(master.items()):
            file.write(f"{reg},{item['name']},{item['department']},{item['email']},"
                       f"{';'.join(item['events'])}\n")

    event_dir = output_folder / "events"
    event_dir.mkdir(exist_ok=True)
    for event, regs in event_map.items():
        with (event_dir / f"{re.sub(r'[^A-Za-z0-9_-]+', '_', event)}.txt").open(
                "w", encoding="utf-8") as file:
            for reg in sorted(regs):
                file.write(f"{reg},{master[reg]['name']}\n")

    with (output_folder / "summary.txt").open("w", encoding="utf-8") as file:
        file.write(f"Total valid unique registrations: {len(master)}\n")
        file.write(f"Number of events: {len(event_map)}\n")
        for event, regs in sorted(event_map.items()):
            file.write(f"{event}: {len(regs)} participants\n")

    (output_folder / "error_log.txt").write_text(
        "\n".join(errors) + ("\n" if errors else ""), encoding="utf-8")
    return master, dict(event_map), errors


# ----------------------------- DEMONSTRATION ---------------------------
def demo():
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)

        # Task 1 demonstration
        mess = root / "mess.txt"
        mess.write_text("192311001,Asha,1250.50\n192311002,Ravi,980\nbad,line\n",
                        encoding="utf-8")
        report, total, rejected = process_mess_file(mess)
        print("TASK 1 REPORT:", report)
        print("TASK 1 TOTAL:", f"{total:.2f}")
        print("TASK 1 REJECTED:", rejected)

        # Task 2 demonstration
        attendance_in = root / "attendance_in"
        attendance_in.mkdir()
        (attendance_in / "day1.csv").write_text(
            "192311001,2026-10-01,P\n192311002,2026-10-01,A\n"
            "damaged,line\n", encoding="utf-8")
        (attendance_in / "day2.csv").write_text(
            "192311001,2026-10-02,P\n192311002,2026-10-02,P\n",
            encoding="utf-8")
        counts, errors = process_attendance_files(attendance_in, root / "attendance_out")
        print("TASK 2 COUNTS:", dict(counts))
        print("TASK 2 ERRORS:", errors)

        # Task 3 demonstration
        sample = root / "sample_attendance.csv"
        sample.write_text(
            "192311001,2026-10-08,P\n192311002,2026-10-08,A\n"
            "192311003,2026-10-08\n192311004,2026-10-08,L\n",
            encoding="utf-8")
        print("TASK 3:", summarise_attendance(sample))

        # Task 4 demonstration: three daily files
        log = root / "returns.log"
        error_log = root / "returns_errors.log"
        for day, books in enumerate((["Book A", "Book B"], ["Book C"], ["Book D"]), 1):
            day_file = root / f"day{day}.txt"
            day_file.write_text("\n".join(books), encoding="utf-8")
            process_return_day(day_file, log, error_log)
        print("TASK 4 LOG:", repr(log.read_text(encoding="utf-8")))

        # Task 5 demonstration
        records = [
            "192311001,2026-10-01,P",
            "192311001,2026-10-02,A",
            "192311001,2026-10-03,A",
            "192311001,2026-10-04,A",
        ]
        parsed = [parse_attendance_line(x) for x in records]
        print("TASK 5 CONSECUTIVE ABSENTEES:", consecutive_absentees(parsed))

        # Task 6 demonstration: five departments; one deliberately missing
        fest_in = root / "fest_in"
        fest_in.mkdir()
        (fest_in / "department1.csv").write_text(
            "192311001,Asha,AIML,asha@example.com,Dance;Music\n"
            "192311001,Asha,AIML,asha@example.com,Dance\n"
            "192311002,Ravi,CSE,invalid-email,Drama\n", encoding="utf-8")
        (fest_in / "department2.csv").write_text(
            "192311003,Meena,ECE,meena@example.com,Music\n"
            "damaged,line\n", encoding="utf-8")
        master, events, fest_errors = process_fest_files(
            fest_in, root / "fest_out",
            ["department1.csv", "department2.csv", "department3.csv",
             "department4.csv", "department5.csv"])
        print("TASK 6 MASTER COUNT:", len(master))
        print("TASK 6 EVENT COUNTS:", {k: len(v) for k, v in events.items()})
        print("TASK 6 ERRORS:", fest_errors)


if __name__ == "__main__":
    demo()
