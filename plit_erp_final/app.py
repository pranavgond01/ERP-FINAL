from flask import Flask, request, redirect, session, flash, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import sqlite3

app = Flask(__name__)
app.secret_key = "plit_erp_secret_change_this"
DB = "plit_erp.db"

COLLEGE = {
    "name": "Pankaj Laddhad Institute of Technology & Management Studies",
    "short": "PLITMS",
    "tagline": "Striving for Excellence in the Quality Professional Education",
    "address": "Chikhli Road, Yelgaon, Buldhana - 443002, Maharashtra",
    "logo": "https://plit.ac.in/wp-content/uploads/2024/01/PLIT-HEader-1-1024x81.jpg"
}


def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def login_required(roles=None):
    def deco(fn):
        @wraps(fn)
        def wrap(*args, **kwargs):
            if "role" not in session:
                return redirect("/")
            if roles and session["role"] not in roles:
                flash("Access denied", "danger")
                return redirect("/")
            return fn(*args, **kwargs)
        return wrap
    return deco


def init_db():
    con = db()
    c = con.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT,
        created_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS courses(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        duration INTEGER
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS subjects(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS students(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        email TEXT UNIQUE,
        roll_no TEXT,
        course TEXT,
        year TEXT,
        semester TEXT,
        admission_year INTEGER,
        passout_year INTEGER,
        phone TEXT,
        address TEXT,
        fees_total INTEGER,
        fees_paid INTEGER,
        created_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS teachers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        email TEXT UNIQUE,
        course TEXT,
        subject TEXT,
        phone TEXT,
        qualification TEXT,
        lectures_taken INTEGER,
        created_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS teacher_subjects(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_id INTEGER,
        course TEXT,
        semester TEXT,
        subject TEXT,
        created_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS student_subjects(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        subject TEXT,
        teacher_name TEXT,
        created_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS marks(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        subject TEXT,
        test_name TEXT,
        marks_obtained INTEGER,
        total_marks INTEGER,
        created_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS attendance(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        subject TEXT,
        total_lectures INTEGER,
        present_lectures INTEGER,
        created_at TEXT
    )""")

    default_courses = [
        ("Computer Science and Engineering", 4),
        ("Civil Engineering", 4),
        ("Mechanical Engineering", 4),
        ("Electrical Engineering", 4),
        ("Electronics and Telecommunication Engineering", 4),
        ("MBA", 2)
    ]

    default_subjects = [
        "Database Management System",
        "Software Engineering",
        "Design and Analysis of Algorithms",
        "Computer Networks",
        "Operating System",
        "Cyber Security",
        "Web Technology",
        "Engineering Mathematics",
        "Data Structures",
        "Artificial Intelligence"
    ]

    for course, duration in default_courses:
        c.execute("INSERT OR IGNORE INTO courses(name,duration) VALUES(?,?)", (course, duration))

    for subject in default_subjects:
        c.execute("INSERT OR IGNORE INTO subjects(name) VALUES(?)", (subject,))

    if not c.execute("SELECT * FROM users WHERE email='admin@plit.ac.in'").fetchone():
        c.execute("INSERT INTO users VALUES(NULL,?,?,?,?,?)",
                  ("Admin", "admin@plit.ac.in", generate_password_hash("admin123"), "admin", now()))

        c.execute("INSERT INTO users VALUES(NULL,?,?,?,?,?)",
                  ("Principal", "principal@plit.ac.in", generate_password_hash("principal123"), "principal", now()))

        c.execute("INSERT INTO users VALUES(NULL,?,?,?,?,?)",
                  ("Demo Teacher", "teacher@plit.ac.in", generate_password_hash("teacher123"), "teacher", now()))
        teacher_user_id = c.lastrowid

        c.execute("INSERT INTO teachers VALUES(NULL,?,?,?,?,?,?,?,?,?)",
                  (
                      teacher_user_id,
                      "Demo Teacher",
                      "teacher@plit.ac.in",
                      "Computer Science and Engineering",
                      "Database Management System",
                      "9876543210",
                      "M.Tech",
                      25,
                      now()
                  ))

        teacher_id = c.lastrowid

        c.execute("INSERT INTO teacher_subjects VALUES(NULL,?,?,?,?,?)",
                  (
                      teacher_id,
                      "Computer Science and Engineering",
                      "6th Semester",
                      "Database Management System",
                      now()
                  ))

        c.execute("INSERT INTO users VALUES(NULL,?,?,?,?,?)",
                  ("Demo Student", "student@plit.ac.in", generate_password_hash("student123"), "student", now()))
        student_user_id = c.lastrowid

        c.execute("INSERT INTO students VALUES(NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                  (
                      student_user_id,
                      "Demo Student",
                      "student@plit.ac.in",
                      "46",
                      "Computer Science and Engineering",
                      "3rd Year",
                      "6th Semester",
                      2023,
                      2027,
                      "9999999999",
                      "Buldhana",
                      50000,
                      30000,
                      now()
                  ))

    con.commit()
    con.close()


def get_common():
    con = db()
    courses = con.execute("SELECT * FROM courses").fetchall()
    subjects = con.execute("SELECT * FROM subjects").fetchall()
    con.close()

    years = ["1st Year", "2nd Year", "3rd Year", "4th Year"]
    semesters = [
        "1st Semester", "2nd Semester", "3rd Semester", "4th Semester",
        "5th Semester", "6th Semester", "7th Semester", "8th Semester"
    ]

    return courses, subjects, years, semesters


BASE = """
<!DOCTYPE html>
<html>
<head>
<title>PLITMS ERP</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
body{background:#eef3fb;font-family:Arial}
.navbar{background:linear-gradient(90deg,#002b5b,#0066cc)}
.hero{background:linear-gradient(135deg,#002b5b,#0d6efd);color:white;padding:25px 0}
.logo{max-width:900px;width:100%;background:white;border-radius:12px;padding:8px;margin-bottom:12px}
.card{border:0;border-radius:16px;box-shadow:0 8px 22px rgba(0,0,0,.08);margin-bottom:22px}
.stat{background:white;border-left:6px solid #0d6efd;padding:18px;border-radius:14px;box-shadow:0 6px 18px rgba(0,0,0,.08)}
.table th{background:#002b5b;color:white;white-space:nowrap}
.table td{white-space:nowrap}
input,select,textarea,.btn{border-radius:10px!important}
</style>
</head>
<body>

<nav class="navbar navbar-dark">
<div class="container-fluid">
<a class="navbar-brand fw-bold" href="/">PLITMS ERP</a>
{% if session.get('role') %}
<span class="text-white">
{{session.get('name')}} | {{session.get('role')|title}}
<a class="btn btn-light btn-sm ms-2" href="/logout">Logout</a>
</span>
{% endif %}
</div>
</nav>

<div class="hero">
<div class="container">
<img src="{{college.logo}}" class="logo">
<h3>{{college.name}}</h3>
<p>{{college.tagline}}</p>
<small>{{college.address}}</small>
</div>
</div>

<div class="container my-4">
{% with messages=get_flashed_messages(with_categories=true) %}
{% for c,m in messages %}
<div class="alert alert-{{c}}">{{m}}</div>
{% endfor %}
{% endwith %}
{{content|safe}}
</div>

</body>
</html>
"""


def page(content):
    return render_template_string(BASE, content=content, college=COLLEGE)


def course_duration(course):
    con = db()
    row = con.execute("SELECT duration FROM courses WHERE name=?", (course,)).fetchone()
    con.close()
    return row["duration"] if row else 4


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        con = db()
        user = con.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        con.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["email"] = user["email"]
            session["role"] = user["role"]
            return redirect("/" + user["role"])

        flash("Invalid login", "danger")

    return page("""
    <div class="row justify-content-center">
    <div class="col-md-5">
    <div class="card p-4">
    <h3 class="text-center text-primary">Login</h3>
    <form method="POST">
    <input class="form-control mb-3" name="email" placeholder="Email" required>
    <input class="form-control mb-3" name="password" type="password" placeholder="Password" required>
    <button class="btn btn-primary w-100">Login</button>
    </form>
    <hr>
    <p><b>Admin:</b> admin@plit.ac.in / admin123</p>
    <p><b>Principal:</b> principal@plit.ac.in / principal123</p>
    <p><b>Teacher:</b> teacher@plit.ac.in / teacher123</p>
    <p><b>Student:</b> student@plit.ac.in / student123</p>
    </div>
    </div>
    </div>
    """)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/admin")
@login_required(["admin"])
def admin():
    con = db()
    principals = con.execute("SELECT * FROM users WHERE role='principal'").fetchall()
    teachers = con.execute("SELECT * FROM teachers").fetchall()
    students = con.execute("SELECT * FROM students").fetchall()
    courses = con.execute("SELECT * FROM courses").fetchall()
    subjects = con.execute("SELECT * FROM subjects").fetchall()
    con.close()

    content = f"""
    <h3>Admin Dashboard</h3>

    <div class="row mb-4">
    <div class="col"><div class="stat">Students<br><b>{len(students)}</b></div></div>
    <div class="col"><div class="stat">Teachers<br><b>{len(teachers)}</b></div></div>
    <div class="col"><div class="stat">Courses<br><b>{len(courses)}</b></div></div>
    <div class="col"><div class="stat">Subjects<br><b>{len(subjects)}</b></div></div>
    </div>

    <div class="card p-3">
    <h5>Add Principal</h5>
    <form action="/admin_add_principal" method="POST" class="row g-2">
    <div class="col-md-4"><input name="name" class="form-control" placeholder="Principal Name" required></div>
    <div class="col-md-4"><input name="email" class="form-control" placeholder="Email" required></div>
    <div class="col-md-4"><input name="password" class="form-control" placeholder="Password" required></div>
    <div><button class="btn btn-primary">Add Principal</button></div>
    </form>
    </div>

    <div class="card p-3">
    <h5>Add / Edit Course</h5>
    <form action="/admin_add_course" method="POST" class="row g-2">
    <div class="col-md-6"><input name="name" class="form-control" placeholder="Course Name" required></div>
    <div class="col-md-3"><input name="duration" type="number" class="form-control" placeholder="Duration Years" required></div>
    <div class="col-md-3"><button class="btn btn-success w-100">Save Course</button></div>
    </form>
    </div>

    <div class="card p-3">
    <h5>Add Subject</h5>
    <form action="/admin_add_subject" method="POST" class="row g-2">
    <div class="col-md-9"><input name="name" class="form-control" placeholder="Subject Name" required></div>
    <div class="col-md-3"><button class="btn btn-success w-100">Add Subject</button></div>
    </form>
    </div>
    """

    content += "<div class='card p-3'><h5>Courses</h5><table class='table table-bordered'><tr><th>Course</th><th>Duration</th></tr>"
    for c in courses:
        content += f"<tr><td>{c['name']}</td><td>{c['duration']} Years</td></tr>"
    content += "</table></div>"

    content += "<div class='card p-3'><h5>Subjects</h5><table class='table table-bordered'><tr><th>Subject</th><th>Delete</th></tr>"
    for s in subjects:
        content += f"<tr><td>{s['name']}</td><td><a class='btn btn-danger btn-sm' href='/delete_subject/{s['id']}'>Delete</a></td></tr>"
    content += "</table></div>"

    return page(content)


@app.route("/principal")
@login_required(["principal"])
def principal():
    con = db()
    students = con.execute("SELECT * FROM students ORDER BY id DESC").fetchall()
    teachers = con.execute("SELECT * FROM teachers ORDER BY id DESC").fetchall()

    teacher_subjects = con.execute("""
        SELECT teacher_subjects.*, teachers.name AS teacher_name, teachers.email AS teacher_email
        FROM teacher_subjects
        JOIN teachers ON teacher_subjects.teacher_id = teachers.id
        ORDER BY teacher_subjects.id DESC
    """).fetchall()

    con.close()

    courses, subjects, years, semesters = get_common()

    teacher_options = "".join([
        f"<option value='{t['id']}'>{t['name']} - {t['email']}</option>"
        for t in teachers
    ])

    course_options = "".join([f"<option>{c['name']}</option>" for c in courses])
    subject_options = "".join([f"<option>{s['name']}</option>" for s in subjects])
    semester_options = "".join([f"<option>{sem}</option>" for sem in semesters])

    content = f"""
    <h3>Principal Dashboard</h3>

    <div class="row mb-4">
    <div class="col"><div class="stat">Students<br><b>{len(students)}</b></div></div>
    <div class="col"><div class="stat">Teachers<br><b>{len(teachers)}</b></div></div>
    </div>

    {student_form(courses, years, semesters)}
    {multi_student_box()}
    {teacher_form(courses, subjects)}
    {multi_teacher_box()}

    <div class="card p-3">
    <h5>Assign Multiple Subjects to Teacher</h5>
    <p class="text-muted">Only principal can assign/edit teacher semester-wise subjects.</p>

    <form action="/assign_teacher_subject" method="POST" class="row g-2">
    <div class="col-md-3">
    <select name="teacher_id" class="form-control" required>
    {teacher_options}
    </select>
    </div>

    <div class="col-md-3">
    <select name="course" class="form-control" required>
    {course_options}
    </select>
    </div>

    <div class="col-md-3">
    <select name="semester" class="form-control" required>
    {semester_options}
    </select>
    </div>

    <div class="col-md-3">
    <select name="subject" class="form-control" required>
    {subject_options}
    </select>
    </div>

    <div class="col-md-12">
    <button class="btn btn-success">Assign Subject</button>
    </div>
    </form>
    </div>
    """

    content += students_table(students, can_delete=True, can_edit=True)
    content += teachers_table(teachers, can_delete=True)

    content += """
    <div class='card p-3'>
    <h5>Teacher Subject Assignments</h5>
    <table class='table table-bordered table-striped'>
    <tr>
    <th>Teacher</th>
    <th>Email</th>
    <th>Course</th>
    <th>Semester</th>
    <th>Subject</th>
    <th>Action</th>
    </tr>
    """

    for ts in teacher_subjects:
        content += f"""
        <tr>
        <td>{ts['teacher_name']}</td>
        <td>{ts['teacher_email']}</td>
        <td>{ts['course']}</td>
        <td>{ts['semester']}</td>
        <td>{ts['subject']}</td>
        <td>
        <a href="/delete_teacher_subject/{ts['id']}" class="btn btn-danger btn-sm">Delete</a>
        </td>
        </tr>
        """

    content += "</table></div>"

    return page(content)


@app.route("/teacher")
@login_required(["teacher"])
def teacher():
    con = db()

    students = con.execute("SELECT * FROM students ORDER BY id DESC").fetchall()

    teacher = con.execute(
        "SELECT * FROM teachers WHERE email=?",
        (session["email"],)
    ).fetchone()

    teacher_subjects = []

    if teacher:
        teacher_subjects = con.execute("""
            SELECT * FROM teacher_subjects
            WHERE teacher_id=?
            ORDER BY semester
        """, (teacher["id"],)).fetchall()

    con.close()

    courses, subjects, years, semesters = get_common()

    content = f"""
    <h3>Teacher Dashboard</h3>

    <div class="row mb-4">
    <div class="col"><div class="stat">Students<br><b>{len(students)}</b></div></div>
    <div class="col"><div class="stat">Lectures Taken<br><b>{teacher['lectures_taken'] if teacher else 0}</b></div></div>
    </div>

    <div class="card p-3">
    <h5>My Assigned Subjects</h5>
    <table class="table table-bordered">
    <tr><th>Course</th><th>Semester</th><th>Subject</th></tr>
    """

    for ts in teacher_subjects:
        content += f"<tr><td>{ts['course']}</td><td>{ts['semester']}</td><td>{ts['subject']}</td></tr>"

    content += """
    </table>
    </div>
    """

    content += f"""
    {student_form(courses, years, semesters)}
    {multi_student_box()}
    {subject_marks_attendance_forms(students, subjects)}
    """

    content += students_table(students, can_delete=True, can_edit=True)

    return page(content)


@app.route("/student")
@login_required(["student"])
def student():
    con = db()

    s = con.execute(
        "SELECT * FROM students WHERE email=?",
        (session["email"],)
    ).fetchone()

    subs = con.execute(
        "SELECT * FROM student_subjects WHERE student_id=?",
        (s["id"],)
    ).fetchall()

    marks = con.execute(
        "SELECT * FROM marks WHERE student_id=?",
        (s["id"],)
    ).fetchall()

    att = con.execute(
        "SELECT * FROM attendance WHERE student_id=?",
        (s["id"],)
    ).fetchall()

    con.close()

    content = f"""
    <h3>Student Dashboard</h3>

    <div class="row mb-4">
    <div class="col"><div class="stat">Total Fees<br><b>₹{s['fees_total']}</b></div></div>
    <div class="col"><div class="stat">Paid Fees<br><b>₹{s['fees_paid']}</b></div></div>
    <div class="col"><div class="stat">Remaining<br><b>₹{s['fees_total'] - s['fees_paid']}</b></div></div>
    </div>

    <div class="card p-3">
    <h5>Student Information</h5>
    <p><b>Name:</b> {s['name']}</p>
    <p><b>Roll:</b> {s['roll_no']}</p>
    <p><b>Course:</b> {s['course']}</p>
    <p><b>Year:</b> {s['year']}</p>
    <p><b>Semester:</b> {s['semester']}</p>
    <p><b>Passout Year:</b> {s['passout_year']}</p>
    </div>
    """

    content += "<div class='card p-3'><h5>Subjects</h5><table class='table table-bordered'><tr><th>Subject</th><th>Teacher</th></tr>"
    for x in subs:
        content += f"<tr><td>{x['subject']}</td><td>{x['teacher_name']}</td></tr>"
    content += "</table></div>"

    content += "<div class='card p-3'><h5>Marks</h5><table class='table table-bordered'><tr><th>Subject</th><th>Test</th><th>Marks</th><th>Total</th></tr>"
    for m in marks:
        content += f"<tr><td>{m['subject']}</td><td>{m['test_name']}</td><td>{m['marks_obtained']}</td><td>{m['total_marks']}</td></tr>"
    content += "</table></div>"

    content += "<div class='card p-3'><h5>Attendance</h5><table class='table table-bordered'><tr><th>Subject</th><th>Total</th><th>Present</th><th>%</th></tr>"
    for a in att:
        per = round((a["present_lectures"] / a["total_lectures"]) * 100, 2) if a["total_lectures"] else 0
        content += f"<tr><td>{a['subject']}</td><td>{a['total_lectures']}</td><td>{a['present_lectures']}</td><td>{per}%</td></tr>"
    content += "</table></div>"

    return page(content)


def student_form(courses, years, semesters):
    course_options = "".join([
        f"<option value='{c['name']}'>{c['name']}</option>"
        for c in courses
    ])

    year_options = "".join([f"<option>{y}</option>" for y in years])
    sem_options = "".join([f"<option>{s}</option>" for s in semesters])

    return f"""
    <div class="card p-3">
    <h5>Add Student</h5>

    <form action="/add_student" method="POST" class="row g-2">
    <div class="col-md-4"><input name="name" class="form-control" placeholder="Name" required></div>
    <div class="col-md-4"><input name="email" class="form-control" placeholder="Email" required></div>
    <div class="col-md-4"><input name="password" class="form-control" placeholder="Password" required></div>

    <div class="col-md-3"><input name="roll_no" class="form-control" placeholder="Roll No" required></div>
    <div class="col-md-3"><select name="course" class="form-control">{course_options}</select></div>
    <div class="col-md-3"><select name="year" class="form-control">{year_options}</select></div>
    <div class="col-md-3"><select name="semester" class="form-control">{sem_options}</select></div>

    <div class="col-md-3"><input name="admission_year" type="number" class="form-control" placeholder="Admission Year" required></div>
    <div class="col-md-3"><input name="phone" class="form-control" placeholder="Phone" required></div>
    <div class="col-md-3"><input name="fees_total" type="number" class="form-control" placeholder="Total Fees" required></div>
    <div class="col-md-3"><input name="fees_paid" type="number" class="form-control" placeholder="Paid Fees" required></div>

    <div class="col-md-12"><input name="address" class="form-control" placeholder="Address" required></div>

    <div><button class="btn btn-success">Add Student</button></div>
    </form>
    </div>
    """


def multi_student_box():
    return """
    <div class="card p-3">
    <h5>Add Multiple Students</h5>
    <p>Format: name,email,password,roll,course,year,semester,admission_year,phone,address,fees_total,fees_paid</p>

    <form action="/multi_add_student" method="POST">
    <textarea name="data" rows="5" class="form-control mb-2"
    placeholder="Rahul,rahul@plit.ac.in,123,47,Computer Science and Engineering,3rd Year,6th Semester,2023,9999999999,Buldhana,50000,30000"></textarea>
    <button class="btn btn-success">Add Multiple Students</button>
    </form>
    </div>
    """


def teacher_form(courses, subjects):
    course_options = "".join([f"<option>{c['name']}</option>" for c in courses])
    subject_options = "".join([f"<option>{s['name']}</option>" for s in subjects])

    return f"""
    <div class="card p-3">
    <h5>Add Teacher</h5>

    <form action="/add_teacher" method="POST" class="row g-2">
    <div class="col-md-4"><input name="name" class="form-control" placeholder="Name" required></div>
    <div class="col-md-4"><input name="email" class="form-control" placeholder="Email" required></div>
    <div class="col-md-4"><input name="password" class="form-control" placeholder="Password" required></div>

    <div class="col-md-4"><select name="course" class="form-control">{course_options}</select></div>
    <div class="col-md-4"><select name="subject" class="form-control">{subject_options}</select></div>
    <div class="col-md-4"><input name="phone" class="form-control" placeholder="Phone" required></div>

    <div class="col-md-6"><input name="qualification" class="form-control" placeholder="Qualification" required></div>
    <div class="col-md-6"><input name="lectures_taken" type="number" class="form-control" placeholder="Lectures Taken" required></div>

    <div><button class="btn btn-primary">Add Teacher</button></div>
    </form>
    </div>
    """


def multi_teacher_box():
    return """
    <div class="card p-3">
    <h5>Add Multiple Teachers</h5>
    <p>Format: name,email,password,course,subject,phone,qualification,lectures</p>

    <form action="/multi_add_teacher" method="POST">
    <textarea name="data" rows="5" class="form-control mb-2"
    placeholder="Amit,amit@plit.ac.in,123,Computer Science and Engineering,DBMS,9999999999,M.Tech,20"></textarea>
    <button class="btn btn-primary">Add Multiple Teachers</button>
    </form>
    </div>
    """


def subject_marks_attendance_forms(students, subjects):
    stu = "".join([
        f"<option value='{s['id']}'>{s['name']} - {s['roll_no']}</option>"
        for s in students
    ])

    sub = "".join([f"<option>{x['name']}</option>" for x in subjects])

    return f"""
    <div class="card p-3">
    <h5>Add Subject / Marks / Attendance</h5>

    <form action="/assign_subject" method="POST" class="row g-2 mb-3">
    <div class="col-md-5"><select name="student_id" class="form-control">{stu}</select></div>
    <div class="col-md-5"><select name="subject" class="form-control">{sub}</select></div>
    <div class="col-md-2"><button class="btn btn-success w-100">Add Subject</button></div>
    </form>

    <form action="/add_marks" method="POST" class="row g-2 mb-3">
    <div class="col-md-3"><select name="student_id" class="form-control">{stu}</select></div>
    <div class="col-md-3"><select name="subject" class="form-control">{sub}</select></div>
    <div class="col-md-2"><input name="test_name" class="form-control" placeholder="Test"></div>
    <div class="col-md-2"><input name="marks_obtained" type="number" class="form-control" placeholder="Marks"></div>
    <div class="col-md-2"><input name="total_marks" type="number" class="form-control" placeholder="Total"></div>
    <div><button class="btn btn-primary">Add Marks</button></div>
    </form>

    <form action="/add_attendance" method="POST" class="row g-2">
    <div class="col-md-3"><select name="student_id" class="form-control">{stu}</select></div>
    <div class="col-md-3"><select name="subject" class="form-control">{sub}</select></div>
    <div class="col-md-3"><input name="total_lectures" type="number" class="form-control" placeholder="Total Lectures"></div>
    <div class="col-md-3"><input name="present_lectures" type="number" class="form-control" placeholder="Present"></div>
    <div><button class="btn btn-warning">Add Attendance</button></div>
    </form>

    </div>
    """


def students_table(students, can_delete=False, can_edit=False):
    html = """
    <div class='card p-3'>
    <h5>Students</h5>
    <table class='table table-bordered table-striped'>
    <tr>
    <th>Name</th>
    <th>Email</th>
    <th>Roll</th>
    <th>Course</th>
    <th>Year</th>
    <th>Sem</th>
    <th>Passout</th>
    <th>Remaining</th>
    <th>Action</th>
    </tr>
    """

    for s in students:
        action = ""

        if can_edit:
            action += f"<a class='btn btn-warning btn-sm me-1' href='/edit_student/{s['id']}'>Edit</a>"

        if can_delete:
            action += f"<a class='btn btn-danger btn-sm' href='/delete_student/{s['id']}'>Delete</a>"

        html += f"""
        <tr>
        <td>{s['name']}</td>
        <td>{s['email']}</td>
        <td>{s['roll_no']}</td>
        <td>{s['course']}</td>
        <td>{s['year']}</td>
        <td>{s['semester']}</td>
        <td>{s['passout_year']}</td>
        <td>₹{s['fees_total'] - s['fees_paid']}</td>
        <td>{action}</td>
        </tr>
        """

    html += "</table></div>"
    return html


def teachers_table(teachers, can_delete=False):
    html = """
    <div class='card p-3'>
    <h5>Teachers</h5>
    <table class='table table-bordered table-striped'>
    <tr>
    <th>Name</th>
    <th>Email</th>
    <th>Course</th>
    <th>Main Subject</th>
    <th>Phone</th>
    <th>Lectures</th>
    <th>Action</th>
    </tr>
    """

    for t in teachers:
        action = ""

        if can_delete:
            action = f"<a class='btn btn-danger btn-sm' href='/delete_teacher/{t['id']}'>Delete</a>"

        html += f"""
        <tr>
        <td>{t['name']}</td>
        <td>{t['email']}</td>
        <td>{t['course']}</td>
        <td>{t['subject']}</td>
        <td>{t['phone']}</td>
        <td>{t['lectures_taken']}</td>
        <td>{action}</td>
        </tr>
        """

    html += "</table></div>"
    return html


@app.route("/add_student", methods=["POST"])
@login_required(["teacher", "principal"])
def add_student():
    d = request.form
    passout = int(d["admission_year"]) + course_duration(d["course"])

    con = db()

    if con.execute("SELECT * FROM users WHERE email=?", (d["email"],)).fetchone():
        flash("Student email already exists", "danger")
        con.close()
        return redirect("/" + session["role"])

    c = con.cursor()

    c.execute("INSERT INTO users VALUES(NULL,?,?,?,?,?)",
              (d["name"], d["email"], generate_password_hash(d["password"]), "student", now()))

    uid = c.lastrowid

    c.execute("INSERT INTO students VALUES(NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (
                  uid,
                  d["name"],
                  d["email"],
                  d["roll_no"],
                  d["course"],
                  d["year"],
                  d["semester"],
                  int(d["admission_year"]),
                  passout,
                  d["phone"],
                  d["address"],
                  int(d["fees_total"]),
                  int(d["fees_paid"]),
                  now()
              ))

    con.commit()
    con.close()

    flash("Student added", "success")
    return redirect("/" + session["role"])


@app.route("/multi_add_student", methods=["POST"])
@login_required(["teacher", "principal"])
def multi_add_student():
    lines = request.form["data"].strip().splitlines()
    count = 0

    for line in lines:
        try:
            name, email, password, roll, course, year, sem, admission, phone, address, total, paid = [
                x.strip() for x in line.split(",")
            ]

            passout = int(admission) + course_duration(course)

            con = db()

            if con.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone():
                con.close()
                continue

            c = con.cursor()

            c.execute("INSERT INTO users VALUES(NULL,?,?,?,?,?)",
                      (name, email, generate_password_hash(password), "student", now()))

            uid = c.lastrowid

            c.execute("INSERT INTO students VALUES(NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                      (
                          uid,
                          name,
                          email,
                          roll,
                          course,
                          year,
                          sem,
                          int(admission),
                          passout,
                          phone,
                          address,
                          int(total),
                          int(paid),
                          now()
                      ))

            con.commit()
            con.close()
            count += 1

        except Exception:
            continue

    flash(f"{count} students added", "success")
    return redirect("/" + session["role"])


@app.route("/add_teacher", methods=["POST"])
@login_required(["principal", "admin"])
def add_teacher():
    d = request.form
    con = db()

    if con.execute("SELECT * FROM users WHERE email=?", (d["email"],)).fetchone():
        flash("Teacher email already exists", "danger")
        con.close()
        return redirect("/" + session["role"])

    c = con.cursor()

    c.execute("INSERT INTO users VALUES(NULL,?,?,?,?,?)",
              (d["name"], d["email"], generate_password_hash(d["password"]), "teacher", now()))

    uid = c.lastrowid

    c.execute("INSERT INTO teachers VALUES(NULL,?,?,?,?,?,?,?,?,?)",
              (
                  uid,
                  d["name"],
                  d["email"],
                  d["course"],
                  d["subject"],
                  d["phone"],
                  d["qualification"],
                  int(d["lectures_taken"]),
                  now()
              ))

    con.commit()
    con.close()

    flash("Teacher added", "success")
    return redirect("/" + session["role"])


@app.route("/multi_add_teacher", methods=["POST"])
@login_required(["principal", "admin"])
def multi_add_teacher():
    lines = request.form["data"].strip().splitlines()
    count = 0

    for line in lines:
        try:
            name, email, password, course, subject, phone, qualification, lectures = [
                x.strip() for x in line.split(",")
            ]

            con = db()

            if con.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone():
                con.close()
                continue

            c = con.cursor()

            c.execute("INSERT INTO users VALUES(NULL,?,?,?,?,?)",
                      (name, email, generate_password_hash(password), "teacher", now()))

            uid = c.lastrowid

            c.execute("INSERT INTO teachers VALUES(NULL,?,?,?,?,?,?,?,?,?)",
                      (
                          uid,
                          name,
                          email,
                          course,
                          subject,
                          phone,
                          qualification,
                          int(lectures),
                          now()
                      ))

            con.commit()
            con.close()
            count += 1

        except Exception:
            continue

    flash(f"{count} teachers added", "success")
    return redirect("/" + session["role"])


@app.route("/assign_teacher_subject", methods=["POST"])
@login_required(["principal"])
def assign_teacher_subject():
    d = request.form

    con = db()

    con.execute("INSERT INTO teacher_subjects VALUES(NULL,?,?,?,?,?)",
                (
                    d["teacher_id"],
                    d["course"],
                    d["semester"],
                    d["subject"],
                    now()
                ))

    con.commit()
    con.close()

    flash("Teacher subject assigned successfully", "success")
    return redirect("/principal")


@app.route("/delete_teacher_subject/<int:id>")
@login_required(["principal"])
def delete_teacher_subject(id):
    con = db()
    con.execute("DELETE FROM teacher_subjects WHERE id=?", (id,))
    con.commit()
    con.close()

    flash("Teacher subject deleted", "success")
    return redirect("/principal")


@app.route("/admin_add_principal", methods=["POST"])
@login_required(["admin"])
def admin_add_principal():
    d = request.form
    con = db()

    if not con.execute("SELECT * FROM users WHERE email=?", (d["email"],)).fetchone():
        con.execute("INSERT INTO users VALUES(NULL,?,?,?,?,?)",
                    (d["name"], d["email"], generate_password_hash(d["password"]), "principal", now()))
        con.commit()

    con.close()
    return redirect("/admin")


@app.route("/admin_add_course", methods=["POST"])
@login_required(["admin"])
def admin_add_course():
    d = request.form
    con = db()

    con.execute("""
        INSERT OR REPLACE INTO courses(id,name,duration)
        VALUES((SELECT id FROM courses WHERE name=?),?,?)
    """, (d["name"], d["name"], int(d["duration"])))

    con.commit()
    con.close()

    flash("Course saved", "success")
    return redirect("/admin")


@app.route("/admin_add_subject", methods=["POST"])
@login_required(["admin"])
def admin_add_subject():
    con = db()
    con.execute("INSERT OR IGNORE INTO subjects(name) VALUES(?)", (request.form["name"],))
    con.commit()
    con.close()

    return redirect("/admin")


@app.route("/delete_subject/<int:id>")
@login_required(["admin"])
def delete_subject(id):
    con = db()
    con.execute("DELETE FROM subjects WHERE id=?", (id,))
    con.commit()
    con.close()

    return redirect("/admin")


@app.route("/delete_student/<int:id>")
@login_required(["teacher", "principal"])
def delete_student(id):
    con = db()

    s = con.execute("SELECT * FROM students WHERE id=?", (id,)).fetchone()

    if s:
        con.execute("DELETE FROM users WHERE email=?", (s["email"],))
        con.execute("DELETE FROM students WHERE id=?", (id,))
        con.execute("DELETE FROM student_subjects WHERE student_id=?", (id,))
        con.execute("DELETE FROM marks WHERE student_id=?", (id,))
        con.execute("DELETE FROM attendance WHERE student_id=?", (id,))

    con.commit()
    con.close()

    flash("Student deleted", "success")
    return redirect("/" + session["role"])


@app.route("/delete_teacher/<int:id>")
@login_required(["principal"])
def delete_teacher(id):
    con = db()

    t = con.execute("SELECT * FROM teachers WHERE id=?", (id,)).fetchone()

    if t:
        con.execute("DELETE FROM users WHERE email=?", (t["email"],))
        con.execute("DELETE FROM teacher_subjects WHERE teacher_id=?", (id,))
        con.execute("DELETE FROM teachers WHERE id=?", (id,))

    con.commit()
    con.close()

    flash("Teacher deleted", "success")
    return redirect("/principal")


@app.route("/edit_student/<int:id>", methods=["GET", "POST"])
@login_required(["teacher", "principal"])
def edit_student(id):
    con = db()
    courses, subjects, years, semesters = get_common()

    if request.method == "POST":
        d = request.form
        passout = int(d["admission_year"]) + course_duration(d["course"])

        con.execute("""
            UPDATE students SET
            name=?,
            email=?,
            roll_no=?,
            course=?,
            year=?,
            semester=?,
            admission_year=?,
            passout_year=?,
            phone=?,
            address=?,
            fees_total=?,
            fees_paid=?
            WHERE id=?
        """, (
            d["name"],
            d["email"],
            d["roll_no"],
            d["course"],
            d["year"],
            d["semester"],
            int(d["admission_year"]),
            passout,
            d["phone"],
            d["address"],
            int(d["fees_total"]),
            int(d["fees_paid"]),
            id
        ))

        con.commit()
        con.close()

        flash("Student updated", "success")
        return redirect("/" + session["role"])

    s = con.execute("SELECT * FROM students WHERE id=?", (id,)).fetchone()
    con.close()

    co = "".join([
        f"<option {'selected' if s['course'] == c['name'] else ''}>{c['name']}</option>"
        for c in courses
    ])

    yo = "".join([
        f"<option {'selected' if s['year'] == y else ''}>{y}</option>"
        for y in years
    ])

    so = "".join([
        f"<option {'selected' if s['semester'] == sem else ''}>{sem}</option>"
        for sem in semesters
    ])

    content = f"""
    <div class="card p-4">
    <h3>Edit Student</h3>

    <form method="POST" class="row g-2">
    <div class="col-md-4"><input name="name" value="{s['name']}" class="form-control"></div>
    <div class="col-md-4"><input name="email" value="{s['email']}" class="form-control"></div>
    <div class="col-md-4"><input name="roll_no" value="{s['roll_no']}" class="form-control"></div>

    <div class="col-md-3"><select name="course" class="form-control">{co}</select></div>
    <div class="col-md-3"><select name="year" class="form-control">{yo}</select></div>
    <div class="col-md-3"><select name="semester" class="form-control">{so}</select></div>
    <div class="col-md-3"><input name="admission_year" type="number" value="{s['admission_year']}" class="form-control"></div>

    <div class="col-md-3"><input name="phone" value="{s['phone']}" class="form-control"></div>
    <div class="col-md-3"><input name="fees_total" value="{s['fees_total']}" class="form-control"></div>
    <div class="col-md-3"><input name="fees_paid" value="{s['fees_paid']}" class="form-control"></div>
    <div class="col-md-12"><input name="address" value="{s['address']}" class="form-control"></div>

    <div>
    <button class="btn btn-primary">Update</button>
    </div>
    </form>
    </div>
    """

    return page(content)


@app.route("/assign_subject", methods=["POST"])
@login_required(["teacher"])
def assign_subject():
    con = db()

    con.execute("INSERT INTO student_subjects VALUES(NULL,?,?,?,?)",
                (
                    request.form["student_id"],
                    request.form["subject"],
                    session["name"],
                    now()
                ))

    con.commit()
    con.close()

    return redirect("/teacher")


@app.route("/add_marks", methods=["POST"])
@login_required(["teacher"])
def add_marks():
    d = request.form
    con = db()

    con.execute("INSERT INTO marks VALUES(NULL,?,?,?,?,?,?)",
                (
                    d["student_id"],
                    d["subject"],
                    d["test_name"],
                    int(d["marks_obtained"]),
                    int(d["total_marks"]),
                    now()
                ))

    con.commit()
    con.close()

    return redirect("/teacher")


@app.route("/add_attendance", methods=["POST"])
@login_required(["teacher"])
def add_attendance():
    d = request.form
    con = db()

    con.execute("INSERT INTO attendance VALUES(NULL,?,?,?,?,?)",
                (
                    d["student_id"],
                    d["subject"],
                    int(d["total_lectures"]),
                    int(d["present_lectures"]),
                    now()
                ))

    con.commit()
    con.close()

    return redirect("/teacher")


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)