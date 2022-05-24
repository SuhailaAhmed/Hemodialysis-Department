"""Hemodialysis Department Website Backend
"""

# Python Imports
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json
import os

# Flask Imports
from flask import Flask, render_template, request, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy
import flask_login as auth

"""The app configurations

1. Flask
2. Flask SQLAlchemy
3. Flask Login
"""

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.secret_key = "qQjnSeZFHN9LVWPl-dB-uw"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

login_manager = auth.LoginManager()
login_manager.init_app(app)


"""The application Database tables

1. Admin    Entities: id, AdminUsername, AdminPassword 
2. Doctor   Entities: DrCounter, DrID, DrName, DrStatus, DrGender
3. Patient  Entities: PatientCounter, PatientID, PatientName,
                      PatientGender, PatientBirthdate
"""


class Admin(db.Model, auth.UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    AdminUsername = db.Column(db.String(250), unique=True, nullable=False)
    AdminPassword = db.Column(db.String(250), unique=False, nullable=False)


class Doctor(db.Model):
    DrCounter = db.Column(db.Integer, unique=True, primary_key=True)
    DrID = db.Column(db.Integer, unique=True)
    DrName = db.Column(db.String(250), unique=False, nullable=False)
    DrStatus = db.Column(db.String(250), unique=False, nullable=False)
    DrGender = db.Column(db.String(250), unique=False, nullable=False)


class Patient(db.Model):
    PatientCounter = db.Column(db.Integer, unique=True, primary_key=True)
    PatientID = db.Column(db.Integer, unique=True)
    PatientName = db.Column(db.String(250), unique=False, nullable=False)
    PatientGender = db.Column(db.String(250), unique=False, nullable=False)
    PatientBirthdate = db.Column(db.DateTime(timezone=True), nullable=False)


"""The application error pages

1. Unauthorized Handler  Unauthorized User error
2. 404                   404 Not found error
"""


@login_manager.unauthorized_handler
def unauthorized():
    flash(f"Please Log-in/Register to access this page.")
    return redirect(url_for("sign_up"))


@app.errorhandler(404)
def page_not_found(error):
    from textwrap import shorten

    return (
        render_template(
            "404.html",
            routes=[rule.rule for rule in app.url_map.iter_rules()],
            message="The page you requested was not found.",
            req_path=shorten(request.path.replace("[...]", "..."), 50)
            if len(request.path.replace("/", " / ")) > 15
            else request.path,
        ),
        404,
    )


"""The application authentication Routes and API

1. Login Manager  For Flask Login
2. Sign Up        Make a new account
3. Sign Out       Sign out of the current account
"""


@login_manager.user_loader
def user_loader(id):
    return Admin.query.get(int(id))


@app.route("/sign-up", methods=["GET", "POST"])
def sign_up():
    if request.method == "GET":
        return render_template("sign_up.html", title="Sign Up")

    if request.method == "POST":
        name = request.form["FullName"]
        pass_code = request.form["Passcode"]
        password_hash = generate_password_hash(
            request.form["Password"], method="pbkdf2:sha256:100_000"
        )
        # pbkdf2:method:iterations

        if pass_code == "QcJ0lHFA":
            new_user = Admin(AdminUsername=name, AdminPassword=password_hash)
        else:
            flash("The Pass Code you enterted was false!")
            return redirect(url_for("sign_up"))

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("home"))


@app.get("/sign-out")
@auth.login_required
def sign_out():
    auth.logout_user()
    return redirect(url_for("home"))


"""The application navs routes

1  /              GET       The root directory (redirects to home)
2. /home          GET POST  The home page
3. /doctor/add    GET POST  Add a new doctor
4. /doctor/view   GET       View the doctors table
5. /patient/add   GET POST  Add a new patient
6. /patient/view  GET       View the patiebts table
7. /contact-us    GET POST  Contact Us form
"""

# 1. The root directory (redirects to home)


@app.get("/")
def index():
    return redirect(url_for("home"))


# 2. The home page


@app.route("/home", methods=["GET", "POST"])
def home():
    if request.method == "GET":
        return render_template("home.html", auth=auth, title="Home")

    if request.method == "POST":
        username = request.form["Name"]
        user = Admin.query.filter_by(AdminUsername=username).first()
        if not check_password_hash(user.AdminPassword, request.form["Password"]):
            flash(f"This password is wrong!")
            return redirect(url_for("home"))
        auth.login_user(user)
        flash(f"Hello, {auth.current_user.AdminUsername}.")
        return redirect(url_for("home"))


# 3. Add a new doctor


@app.route("/doctor/add", methods=["POST", "GET"])
@auth.login_required
def add_doctor():
    if request.method == "GET":
        return render_template("add_doctor.html", auth=auth, title="Add Doctor")

    if request.method == "POST":
        name = request.form["name"]
        id = request.form["id"]
        status = request.form["status"]
        gender = request.form["gender"]

        new_doctor = Doctor(DrID=id, DrName=name, DrStatus=status, DrGender=gender)

        db.session.add(new_doctor)
        db.session.commit()

        with open(f"{BASE_DIR}/app.json", "r") as data:
            dpdata = json.load(data)
        current_month = int(datetime.today().strftime("%m")) - 5
        dpdata["doctors"][current_month] += 1
        with open(f"{BASE_DIR}/app.json", "w") as data:
            data.write(json.dumps(dpdata))

        return redirect(url_for("view_doctor"))


# 4. View the doctors table


@app.get("/doctor/view")
@auth.login_required
def view_doctor():
    rows = Doctor.query.all()
    return render_template(
        "view_doctor.html", rows=rows, auth=auth, title="View Doctors"
    )


@app.route("/doctor/edit", methods=["POST", "GET"])
@auth.login_required
def edit_doctor():
    doctor = Doctor.query.filter_by(DrID=request.args.get("id")).first()

    if request.method == "GET":
        return render_template(
            "edit_doctor.html", auth=auth, doctor=doctor, title="Edit Doctor"
        )

    if request.method == "POST":
        doctor.DrName = request.form["name"]
        doctor.DrStatus = request.form["status"]
        doctor.DrGender = request.form["gender"]

        db.session.commit()

        return redirect(url_for("view_doctor"))


@app.get("/doctor/delete")
@auth.login_required
def delete_doctor():
    Doctor.query.filter_by(DrID=request.args.get("id")).delete()

    db.session.commit()

    return redirect(url_for("view_doctor"))


# 5. Add a new patient
@app.route("/patient/add", methods=["POST", "GET"])
@auth.login_required
def add_patient():
    if request.method == "GET":
        return render_template("add_patient.html", auth=auth, title="Add Patient")

    if request.method == "POST":
        name = request.form["name"]
        id = request.form["id"]
        date = request.form["date"]
        gender = request.form["gender"]

        datetime_date = datetime(
            year=int(date.split("-")[0]),
            month=int(date.split("-")[1]),
            day=int(date.split("-")[2]),
        )

        new_patient = Patient(
            PatientID=id,
            PatientName=name,
            PatientGender=gender,
            PatientBirthdate=datetime_date,
        )

        db.session.add(new_patient)
        db.session.commit()

        with open(f"{BASE_DIR}/app.json", "r") as data:
            dpdata = json.load(data)
        current_month = int(datetime.today().strftime("%m")) - 5
        dpdata["patients"][current_month] += 1
        with open(f"{BASE_DIR}/app.json", "w") as data:
            data.write(json.dumps(dpdata))

        return redirect(url_for("view_patient"))


# 6. View the patients table


@app.get("/patient/view")
@auth.login_required
def view_patient():
    rows = Patient.query.all()
    return render_template(
        "view_patient.html", rows=rows, auth=auth, title="View Patients"
    )


@app.route("/patient/edit", methods=["POST", "GET"])
@auth.login_required
def edit_patient():
    patient = Patient.query.filter_by(PatientID=request.args.get("id")).first()

    if request.method == "GET":
        return render_template(
            "edit_patient.html", auth=auth, patient=patient, title="Edit Patient"
        )

    if request.method == "POST":
        patient.PatientName = request.form["name"]
        patient.PatientGender = request.form["gender"]
        patient.PatientBirthdate = datetime(
            year=int(request.form["date"].split("-")[0]),
            month=int(request.form["date"].split("-")[1]),
            day=int(request.form["date"].split("-")[2]),
        )

        db.session.commit()

        return redirect(url_for("view_patient"))


@app.get("/patient/delete")
@auth.login_required
def delete_patient():
    Patient.query.filter_by(PatientID=request.args.get("id")).delete()

    db.session.commit()

    return redirect(url_for("view_patient"))


# 7. Contact Us form


@app.route("/contact-us", methods=["GET", "POST"])
def contact_us():
    if request.method == "GET":
        return render_template("contact_us.html", auth=auth, title="Contact Us")

    if request.method == "POST":
        with open(f"{BASE_DIR}/app.json", "r") as data:
            dpdata = json.load(data)

        dpdata["messages"].append(
            {
                "name": request.form["name"],
                "email": request.form["email"],
                "message": request.form["message"],
            }
        )

        with open(f"{BASE_DIR}/app.json", "w") as data:
            data.write(json.dumps(dpdata))

        flash("Your message has been sent sucessfully!")
        return redirect(url_for("contact_us"))


@app.get("/analysis")
@auth.login_required
def analysis():
    with open(f"{BASE_DIR}/app.json", "r") as data:
        dpdata = json.load(data)
    return render_template("analysis.html", auth=auth, title="Analysis", data=dpdata)


@app.get("/messages")
@auth.login_required
def messages():
    with open(f"{BASE_DIR}/app.json", "r") as data:
        messages = json.load(data)["messages"]
    return render_template(
        "messasges.html",
        auth=auth,
        title="Messages",
        messages=messages,
        enumerate=enumerate,
    )


@app.get("/messages/delete")
@auth.login_required
def messages_delete():
    with open(f"{BASE_DIR}/app.json", "r") as data:
        data = json.load(data)

    data["messages"].pop(int(request.args.get("ind")))

    with open(f"{BASE_DIR}/app.json", "w") as bsdata:
        bsdata.write(json.dumps(data))

    return redirect(url_for("messages"))


db.create_all()
