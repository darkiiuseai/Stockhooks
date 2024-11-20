import os
import threading
import zipfile
from flask import Flask, request, send_from_directory, jsonify
from tkinter import Tk, Label, Entry, Button, Listbox, filedialog, StringVar, messagebox, Toplevel
from tkinter import ttk

# Configuration initiale
app = Flask(__name__)
UPLOAD_FOLDER = "received_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

received_files = []  # Liste des fichiers reçus
ALLOWED_EXTENSIONS = {'.txt', '.jpg', '.png', '.pdf'}  # Extensions acceptées
AUTH_TOKEN = "secure_token_12345"  # Jeton d'authentification

@app.route("/", methods=["POST"])
def webhook():
    """Endpoint pour recevoir les fichiers via le webhook"""
    # Vérification de l'authentification
    token = request.headers.get("Authorization")
    if token != AUTH_TOKEN:
        return jsonify({"error": "Accès non autorisé"}), 403

    if "file" not in request.files:
        return jsonify({"error": "Aucun fichier trouvé"}), 400

    uploaded_file = request.files["file"]
    if uploaded_file.filename == "":
        return jsonify({"error": "Nom de fichier vide"}), 400

    # Filtrage par extension
    _, ext = os.path.splitext(uploaded_file.filename)
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"error": f"Type de fichier non autorisé : {ext}"}), 400

    # Sauvegarde du fichier
    save_path = os.path.join(UPLOAD_FOLDER, uploaded_file.filename)
    uploaded_file.save(save_path)
    received_files.append(uploaded_file.filename)  # Ajouter à la liste
    print(f"Fichier reçu et enregistré : {save_path}")
    return jsonify({"message": f"Fichier reçu : {uploaded_file.filename}"}), 200

@app.route("/files/<filename>", methods=["GET"])
def get_file(filename):
    """Endpoint pour récupérer un fichier par son nom"""
    if os.path.exists(os.path.join(UPLOAD_FOLDER, filename)):
        return send_from_directory(UPLOAD_FOLDER, filename)
    return jsonify({"error": "Fichier non trouvé"}), 404

@app.route("/files", methods=["GET"])
def download_all_files():
    """Télécharge tous les fichiers sous forme d'archive ZIP"""
    zip_filename = "all_files.zip"
    zip_filepath = os.path.join(UPLOAD_FOLDER, zip_filename)

    with zipfile.ZipFile(zip_filepath, "w") as zipf:
        for root, _, files in os.walk(UPLOAD_FOLDER):
            for file in files:
                if file != zip_filename:  # Éviter d'ajouter l'archive elle-même
                    zipf.write(os.path.join(root, file), arcname=file)

    return send_from_directory(UPLOAD_FOLDER, zip_filename)

# Thread pour exécuter Flask
def run_flask():
    app.run(port=5000)

# Interface graphique Tkinter
class WebhookApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Recevoir des fichiers via Webhook")
        self.folder = StringVar(value=UPLOAD_FOLDER)

        # Champs pour l'URL du webhook
        Label(root, text="URL du Webhook :").pack()
        self.url_entry = Entry(root, width=50)
        self.url_entry.pack()

        # Bouton pour démarrer le serveur
        Button(root, text="Démarrer le serveur", command=self.start_server).pack()

        # Choisir le dossier de stockage
        Label(root, text="Dossier de stockage :").pack()
        self.folder_label = Label(root, textvariable=self.folder)
        self.folder_label.pack()
        Button(root, text="Changer de dossier", command=self.change_folder).pack()

        # Liste des fichiers reçus
        Label(root, text="Fichiers reçus :").pack()
        self.file_listbox = Listbox(root, width=50)
        self.file_listbox.pack()

        # Boutons pour interagir avec les fichiers
        Button(root, text="Ouvrir le fichier sélectionné", command=self.open_selected_file).pack()
        Button(root, text="Obtenir l'URL du fichier", command=self.get_file_url).pack()
        Button(root, text="Supprimer le fichier sélectionné", command=self.delete_selected_file).pack()
        Button(root, text="Télécharger tous les fichiers en ZIP", command=self.download_all).pack()
        Button(root, text="Ouvrir le dossier", command=self.open_folder).pack()

        # Compteur des fichiers reçus
        self.file_count_label = Label(root, text="Fichiers reçus : 0")
        self.file_count_label.pack()

    def start_server(self):
        """Démarre le serveur Flask"""
        webhook_url = self.url_entry.get()
        if webhook_url:
            print(f"Webhook configuré pour : {webhook_url}")
        threading.Thread(target=run_flask, daemon=True).start()
        print("Serveur démarré sur le port 5000")

    def change_folder(self):
        """Changer le dossier de stockage"""
        new_folder = filedialog.askdirectory()
        if new_folder:
            self.folder.set(new_folder)
            global UPLOAD_FOLDER
            UPLOAD_FOLDER = new_folder
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            print(f"Nouveau dossier de stockage : {UPLOAD_FOLDER}")

    def open_selected_file(self):
        """Ouvre le fichier sélectionné"""
        selected = self.file_listbox.curselection()
        if selected:
            filename = self.file_listbox.get(selected)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            os.startfile(file_path)
        else:
            messagebox.showwarning("Alerte", "Veuillez sélectionner un fichier")

    def delete_selected_file(self):
        """Supprime le fichier sélectionné"""
        selected = self.file_listbox.curselection()
        if selected:
            filename = self.file_listbox.get(selected)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            os.remove(file_path)
            self.file_listbox.delete(selected)
            self.update_file_count()
            messagebox.showinfo("Succès", f"Fichier {filename} supprimé")

    def download_all(self):
        """Télécharge tous les fichiers en ZIP"""
        zip_url = f"http://localhost:5000/files/all_files.zip"
        self.show_url_popup(zip_url)

    def get_file_url(self):
        """Obtient l'URL du fichier sélectionné"""
        selected = self.file_listbox.curselection()
        if selected:
            filename = self.file_listbox.get(selected)
            file_url = f"http://localhost:5000/files/{filename}"
            self.show_url_popup(file_url)

    def show_url_popup(self, url):
        """Affiche un popup avec l'URL du fichier"""
        popup = Toplevel(self.root)
        popup.title("URL")
        Label(popup, text="Voici l'URL :").pack()
        Entry(popup, width=50, state="readonly", readonlybackground="white", fg="black", textvariable=StringVar(value=url)).pack()

    def update_file_count(self):
        """Met à jour le compteur des fichiers"""
        count = self.file_listbox.size()
        self.file_count_label.config(text=f"Fichiers reçus : {count}")

# Lancement de l'application
if __name__ == "__main__":
    root = Tk()
    app = WebhookApp(root)

    # Synchroniser les fichiers reçus
    threading.Thread(target=lambda: None, daemon=True).start()

    root.mainloop()
