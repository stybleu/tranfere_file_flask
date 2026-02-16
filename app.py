import os
from datetime import datetime
from flask import Flask, request, send_from_directory, render_template, redirect, url_for, flash, abort
from werkzeug.utils import secure_filename

# -----------------------
# Configuration
# -----------------------
UPLOAD_FOLDER = "fichiers"
MAX_CONTENT_LENGTH = 512 * 1024 * 1024  # 512 Mo max
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
app.secret_key = "cle-secrete-pour-flash"  # juste pour afficher des messages

# -----------------------
# Fonctions utilitaires
# -----------------------
def human_size(n: int) -> str:
    units = ["o", "Ko", "Mo", "Go", "To"]
    i = 0
    f = float(n)
    while f >= 1024 and i < len(units) - 1:
        f /= 1024.0
        i += 1
    return f"{f:.2f} {units[i]}" if i > 0 else f"{int(f)} {units[i]}"

def list_files():
    items = []
    with os.scandir(UPLOAD_FOLDER) as it:
        for entry in it:
            if entry.is_file():
                stat = entry.stat()
                items.append({
                    "name": entry.name,
                    "size_h": human_size(stat.st_size),
                    "mtime_h": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                })
    items.sort(key=lambda x: x["mtime_h"], reverse=True)
    return items

# -----------------------
# Routes
# -----------------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        files = request.files.getlist("files")
        if not files or files == [None]:
            flash(("warning", "Aucun fichier sélectionné."))
            return redirect(url_for("index"))

        saved = 0
        for f in files:
            if not f or f.filename == "":
                continue
            filename = secure_filename(f.filename)
            f.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            saved += 1

        flash(("success", f"{saved} fichier(s) téléversé(s) avec succès."))
        return redirect(url_for("index"))

    return render_template("index.html", files=list_files(), max_mb=int(MAX_CONTENT_LENGTH / (1024*1024)))

@app.route("/download/<path:filename>")
def download(filename):
    filename = os.path.basename(filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if not os.path.isfile(file_path):
        abort(404)
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)

@app.route("/delete", methods=["POST"])
def delete_file():
    filename = os.path.basename(request.form.get("filename", ""))
    if not filename:
        flash(("warning", "Nom de fichier manquant."))
        return redirect(url_for("index"))

    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if os.path.isfile(path):
        os.remove(path)
        flash(("success", f"« {filename} » supprimé."))
    else:
        flash(("warning", "Fichier introuvable."))
    return redirect(url_for("index"))

# -----------------------
# Lancement
# -----------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)