import io
import os
import threading

from dotenv import load_dotenv

load_dotenv()

from flask import Flask, jsonify, request, send_file

from services import email_reader, excel_writer, extractor

app = Flask(__name__, static_folder="static", static_url_path="")

_lock = threading.Lock()
_job = {
    "running": False,
    "total": 0,
    "done": 0,
    "results": [],
    "summary": None,
    "error": None,
    "download_bytes": None,
}


@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/api/health")
def health():
    return jsonify({"groq_key_configured": bool(os.environ.get("GROQ_API_KEY"))})


def _show_dialog(pick_fn):
    """Run a tkinter folder picker dialog on top of other windows and return the chosen path."""
    import tkinter as tk

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        path = pick_fn(parent=root)
    finally:
        root.destroy()
    return path or ""


@app.route("/api/browse-folder")
def browse_folder():
    from tkinter import filedialog

    path = _show_dialog(lambda parent: filedialog.askdirectory(parent=parent, title="Select emails folder"))
    return jsonify({"path": path})


def _run_job(folder_path: str, email_files: list):
    results = []
    rows = []
    for filename in email_files:
        full_path = os.path.join(folder_path, filename)
        try:
            data = email_reader.parse_email_file(full_path)
            fields = extractor.extract_fields(data)
            rows.append(fields)
            results.append({"filename": filename, "status": "processed", **fields})
        except Exception as exc:
            results.append({"filename": filename, "status": "error", "error": str(exc)})

        with _lock:
            _job["done"] += 1
            _job["results"] = list(results)

    download_bytes = excel_writer.build_workbook_bytes(rows) if rows else None

    with _lock:
        _job["summary"] = {
            "total_found": len(email_files),
            "processed": sum(1 for r in results if r["status"] == "processed"),
            "errors": sum(1 for r in results if r["status"] == "error"),
        }
        _job["download_bytes"] = download_bytes
        _job["running"] = False


@app.route("/api/run", methods=["POST"])
def run():
    payload = request.get_json(force=True) or {}
    folder_path = (payload.get("folder_path") or "").strip().strip('"')

    if not os.path.isdir(folder_path):
        return jsonify({"error": f"Folder not found: {folder_path}"}), 400
    if not os.environ.get("GROQ_API_KEY"):
        return jsonify({"error": "GROQ_API_KEY not set. Add it to .env and restart the server."}), 500

    with _lock:
        if _job["running"]:
            return jsonify({"error": "A parsing run is already in progress."}), 409

        email_files = sorted(
            f for f in os.listdir(folder_path) if f.lower().endswith((".eml", ".msg"))
        )

        _job.update(
            {
                "running": True,
                "total": len(email_files),
                "done": 0,
                "results": [],
                "summary": None,
                "error": None,
                "download_bytes": None,
            }
        )

    thread = threading.Thread(target=_run_job, args=(folder_path, email_files), daemon=True)
    thread.start()

    return jsonify({"started": True, "total": len(email_files)})


@app.route("/api/progress")
def progress():
    with _lock:
        return jsonify(
            {
                "running": _job["running"],
                "total": _job["total"],
                "done": _job["done"],
                "results": _job["results"],
                "summary": _job["summary"],
                "download_ready": _job["download_bytes"] is not None,
            }
        )


@app.route("/api/download")
def download():
    with _lock:
        data = _job["download_bytes"]
    if not data:
        return jsonify({"error": "No parsed results available to download yet."}), 404
    return send_file(
        io.BytesIO(data),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="parsed_emails.xlsx",
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000, threaded=True)
