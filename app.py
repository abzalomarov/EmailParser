import io
import os
import tempfile

from dotenv import load_dotenv

load_dotenv()

from flask import Flask, jsonify, request, send_file

from services import email_reader, excel_writer, extractor

app = Flask(__name__, static_folder="static", static_url_path="")

ALLOWED_EXTENSIONS = (".eml", ".msg")


@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/api/health")
def health():
    return jsonify({"groq_key_configured": bool(os.environ.get("GROQ_API_KEY"))})


@app.route("/api/parse-one", methods=["POST"])
def parse_one():
    if not os.environ.get("GROQ_API_KEY"):
        return jsonify({"error": "GROQ_API_KEY not set on the server."}), 500

    upload = request.files.get("file")
    if upload is None or not upload.filename:
        return jsonify({"error": "No file uploaded."}), 400

    filename = upload.filename
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"filename": filename, "status": "error", "error": f"Unsupported file type: {ext}"})

    fd, tmp_path = tempfile.mkstemp(suffix=ext)
    try:
        with os.fdopen(fd, "wb") as f:
            upload.save(f)
        data = email_reader.parse_email_file(tmp_path)
        data["filename"] = filename
        fields = extractor.extract_fields(data)
        return jsonify({"filename": filename, "status": "processed", **fields})
    except Exception as exc:
        return jsonify({"filename": filename, "status": "error", "error": str(exc)})
    finally:
        os.remove(tmp_path)


@app.route("/api/generate-excel", methods=["POST"])
def generate_excel():
    payload = request.get_json(force=True) or {}
    rows = payload.get("rows") or []
    if not rows:
        return jsonify({"error": "No rows to include in the file."}), 400

    data = excel_writer.build_workbook_bytes(rows)
    return send_file(
        io.BytesIO(data),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="parsed_emails.xlsx",
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
