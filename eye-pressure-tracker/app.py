import datetime
import os

from dotenv import load_dotenv

load_dotenv()

from flask import Flask, render_template, request, send_file, redirect, url_for, flash
import io

import db
import vision
from excel_export import build_workbook
from email_sender import send_excel_email

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

db.init_db()

ALLOWED_TYPES = {
    "image/jpeg": "image/jpeg",
    "image/png": "image/png",
    "image/webp": "image/webp",
    "image/heic": "image/heic",
}


@app.route("/")
def index():
    return render_template("upload.html")


@app.route("/process", methods=["POST"])
def process():
    photo = request.files.get("photo")
    if not photo or photo.filename == "":
        flash("Please choose or take a photo first.")
        return redirect(url_for("index"))

    media_type = ALLOWED_TYPES.get(photo.mimetype, "image/jpeg")
    image_bytes = photo.read()

    now = datetime.datetime.now()
    extracted = {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M"),
        "pressure_left": "",
        "pressure_right": "",
    }

    try:
        result = vision.extract_reading(image_bytes, media_type)
        if result.get("date"):
            extracted["date"] = result["date"]
        if result.get("time"):
            extracted["time"] = result["time"]
        if result.get("pressure_left") is not None:
            extracted["pressure_left"] = result["pressure_left"]
        if result.get("pressure_right") is not None:
            extracted["pressure_right"] = result["pressure_right"]
    except Exception as exc:
        flash(f"Could not automatically read the photo ({exc}). Please fill in the values below.")

    return render_template("confirm.html", reading=extracted)


@app.route("/save", methods=["POST"])
def save():
    date = request.form.get("date", "").strip()
    time = request.form.get("time", "").strip()
    pressure_left = request.form.get("pressure_left", "").strip()
    pressure_right = request.form.get("pressure_right", "").strip()

    if not date or not time:
        flash("Date and time are required.")
        return redirect(url_for("index"))

    db.add_reading(date, time, pressure_left or None, pressure_right or None)

    readings = db.get_all_readings()
    excel_bytes = build_workbook(readings)

    email_error = None
    try:
        send_excel_email(excel_bytes)
    except Exception as exc:
        email_error = str(exc)

    return render_template("success.html", email_error=email_error)


@app.route("/history")
def history():
    readings = db.get_all_readings()
    return render_template("history.html", readings=readings)


@app.route("/download")
def download():
    readings = db.get_all_readings()
    excel_bytes = build_workbook(readings)
    return send_file(
        io.BytesIO(excel_bytes),
        as_attachment=True,
        download_name="eye_pressure_readings.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
