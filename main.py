"""
Étape 7 - Élèves & Notes (module complet)
============================================
Ajoute :
    - Gestion des classes
    - Gestion des élèves (nom, prénom, classe, photo)
    - Gestion des matières (avec coefficient)
    - Saisie des notes par trimestre (1, 2, 3)
    - Appréciation par trimestre
    - Calcul automatique de la moyenne (pondérée par les coefficients)

Comment l'utiliser :
    1. Mets ce fichier dans le même dossier que "logo.png"
    2. Ouvre-le dans Pydroid3
    3. Appuie sur "Interpreter" (▶) pour le lancer

Compte de test créé automatiquement :
    E-mail    : test@test.com
    Mot de passe : 1234
    Question  : Nom de ton premier animal ?
    Réponse   : medor
"""

import sqlite3
import hashlib
import os
import shutil

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.filechooser import FileChooserIconView
from kivy.core.window import Window
from kivy.metrics import dp

Window.clearcolor = (0.95, 0.96, 0.98, 1)

DOSSIER = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(DOSSIER, "logo.png")
DB_PATH = os.path.join(DOSSIER, "ecole.db")
DOSSIER_PHOTOS = os.path.join(DOSSIER, "photos_eleves")
os.makedirs(DOSSIER_PHOTOS, exist_ok=True)

TRIMESTRES = ["Trimestre 1", "Trimestre 2", "Trimestre 3"]


def popup_info(titre, message):
    Popup(title=titre, content=Label(text=message), size_hint=(0.85, 0.4)).open()


def hacher(texte):
    return hashlib.sha256(texte.encode("utf-8")).hexdigest()


def normaliser(texte):
    return texte.strip().lower()


# -----------------------------------------------------------------
# BASE DE DONNÉES
# -----------------------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS utilisateurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT, prenom TEXT, email TEXT UNIQUE NOT NULL, ecole TEXT,
            mot_de_passe_hash TEXT NOT NULL,
            question_secrete TEXT, reponse_secrete_hash TEXT
        )
    """)
    c.execute("PRAGMA table_info(utilisateurs)")
    colonnes = [ligne[1] for ligne in c.fetchall()]
    for nom_colonne, type_colonne in [
        ("nom", "TEXT"), ("prenom", "TEXT"), ("ecole", "TEXT"),
        ("question_secrete", "TEXT"), ("reponse_secrete_hash", "TEXT"),
    ]:
        if nom_colonne not in colonnes:
            c.execute(f"ALTER TABLE utilisateurs ADD COLUMN {nom_colonne} {type_colonne}")

    c.execute("SELECT COUNT(*) FROM utilisateurs")
    if c.fetchone()[0] == 0:
        c.execute(
            """INSERT INTO utilisateurs
               (nom, prenom, email, ecole, mot_de_passe_hash, question_secrete, reponse_secrete_hash)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            ("Test", "Utilisateur", "test@test.com", "École Test", hacher("1234"),
             "Nom de ton premier animal ?", hacher(normaliser("medor")))
        )

    c.execute("""
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT UNIQUE NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS eleves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            prenom TEXT NOT NULL,
            classe_id INTEGER,
            photo TEXT,
            FOREIGN KEY(classe_id) REFERENCES classes(id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS matieres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT UNIQUE NOT NULL,
            coefficient REAL NOT NULL DEFAULT 1
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            eleve_id INTEGER,
            matiere_id INTEGER,
            trimestre TEXT,
            note REAL,
            FOREIGN KEY(eleve_id) REFERENCES eleves(id),
            FOREIGN KEY(matiere_id) REFERENCES matieres(id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS appreciations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            eleve_id INTEGER,
            trimestre TEXT,
            texte TEXT,
            FOREIGN KEY(eleve_id) REFERENCES eleves(id)
        )
    """)
    conn.commit()
    conn.close()


def verifier_utilisateur(email, mot_de_passe):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id FROM utilisateurs WHERE email=? AND mot_de_passe_hash=?",
              (email.lower().strip(), hacher(mot_de_passe)))
    row = c.fetchone()
    conn.close()
    return row is not None


def obtenir_prenom(email):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT prenom FROM utilisateurs WHERE email=?", (email.lower().strip(),))
    row = c.fetchone()
    conn.close()
    return row[0] if row and row[0] else "utilisateur"


def creer_utilisateur(nom, prenom, email, ecole, mot_de_passe, question, reponse):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    reponse_hash = hacher(normaliser(reponse)) if reponse else None
    try:
        c.execute(
            """INSERT INTO utilisateurs
               (nom, prenom, email, ecole, mot_de_passe_hash, question_secrete, reponse_secrete_hash)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (nom, prenom, email.lower().strip(), ecole, hacher(mot_de_passe),
             question, reponse_hash)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def obtenir_question(email):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT question_secrete FROM utilisateurs WHERE email=?", (email.lower().strip(),))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None


def verifier_reponse(email, reponse):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT reponse_secrete_hash FROM utilisateurs WHERE email=?", (email.lower().strip(),))
    row = c.fetchone()
    conn.close()
    if row is None or row[0] is None:
        return False
    return row[0] == hacher(normaliser(reponse))


def reinitialiser_mdp(email, nouveau_mdp):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE utilisateurs SET mot_de_passe_hash=? WHERE email=?",
              (hacher(nouveau_mdp), email.lower().strip()))
    conn.commit()
    conn.close()


# --- Classes ---
def ajouter_classe(nom):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO classes (nom) VALUES (?)", (nom,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def liste_classes():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, nom FROM classes ORDER BY nom")
    rows = c.fetchall()
    conn.close()
    return rows


def supprimer_classe(classe_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM classes WHERE id=?", (classe_id,))
    conn.commit()
    conn.close()


# --- Matières ---
def ajouter_matiere(nom, coefficient):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO matieres (nom, coefficient) VALUES (?, ?)", (nom, coefficient))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def liste_matieres():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, nom, coefficient FROM matieres ORDER BY nom")
    rows = c.fetchall()
    conn.close()
    return rows


def supprimer_matiere(matiere_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM matieres WHERE id=?", (matiere_id,))
    conn.commit()
    conn.close()


# --- Élèves ---
def ajouter_eleve(nom, prenom, classe_id, photo):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO eleves (nom, prenom, classe_id, photo) VALUES (?, ?, ?, ?)",
              (nom, prenom, classe_id, photo))
    conn.commit()
    conn.close()


def liste_eleves():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT eleves.id, eleves.nom, eleves.prenom, classes.nom, eleves.photo
        FROM eleves LEFT JOIN classes ON eleves.classe_id = classes.id
        ORDER BY eleves.nom
    """)
    rows = c.fetchall()
    conn.close()
    return rows


def supprimer_eleve(eleve_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM notes WHERE eleve_id=?", (eleve_id,))
    c.execute("DELETE FROM appreciations WHERE eleve_id=?", (eleve_id,))
    c.execute("DELETE FROM eleves WHERE id=?", (eleve_id,))
    conn.commit()
    conn.close()


# --- Notes & appréciations ---
def enregistrer_note(eleve_id, matiere_id, trimestre, note):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id FROM notes WHERE eleve_id=? AND matiere_id=? AND trimestre=?",
              (eleve_id, matiere_id, trimestre))
    row = c.fetchone()
    if row:
        c.execute("UPDATE notes SET note=? WHERE id=?", (note, row[0]))
    else:
        c.execute("INSERT INTO notes (eleve_id, matiere_id, trimestre, note) VALUES (?, ?, ?, ?)",
                  (eleve_id, matiere_id, trimestre, note))
    conn.commit()
    conn.close()


def notes_eleve_trimestre(eleve_id, trimestre):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT matieres.id, matieres.nom, matieres.coefficient, notes.note
        FROM matieres
        LEFT JOIN notes ON notes.matiere_id = matieres.id
            AND notes.eleve_id=? AND notes.trimestre=?
        ORDER BY matieres.nom
    """, (eleve_id, trimestre))
    rows = c.fetchall()
    conn.close()
    return rows  # (matiere_id, nom, coefficient, note ou None)


def calculer_moyenne(eleve_id, trimestre):
    rows = notes_eleve_trimestre(eleve_id, trimestre)
    total_points = 0
    total_coeff = 0
    for _, _, coeff, note in rows:
        if note is not None:
            total_points += note * coeff
            total_coeff += coeff
    if total_coeff == 0:
        return None
    return total_points / total_coeff


def enregistrer_appreciation(eleve_id, trimestre, texte):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id FROM appreciations WHERE eleve_id=? AND trimestre=?", (eleve_id, trimestre))
    row = c.fetchone()
    if row:
        c.execute("UPDATE appreciations SET texte=? WHERE id=?", (texte, row[0]))
    else:
        c.execute("INSERT INTO appreciations (eleve_id, trimestre, texte) VALUES (?, ?, ?)",
                  (eleve_id, trimestre, texte))
    conn.commit()
    conn.close()


def obtenir_appreciation(eleve_id, trimestre):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT texte FROM appreciations WHERE eleve_id=? AND trimestre=?", (eleve_id, trimestre))
    row = c.fetchone()
    conn.close()
    return row[0] if row else ""


# -----------------------------------------------------------------
# WIDGETS COMMUNS
# -----------------------------------------------------------------
class HeaderLogo(BoxLayout):
    def __init__(self, titre="", **kwargs):
        super().__init__(orientation="vertical", size_hint_y=None, height=dp(90) if not titre else dp(120), **kwargs)
        if os.path.exists(LOGO_PATH):
            logo = Image(source=LOGO_PATH, size_hint=(None, None), size=(dp(70), dp(70)),
                         pos_hint={"center_x": 0.5})
            self.add_widget(logo)
        if titre:
            self.add_widget(Label(text=titre, font_size=dp(20), bold=True,
                                  color=(0.1, 0.1, 0.1, 1), size_hint_y=None, height=dp(35)))


def bouton_retour(manager, ecran_cible):
    btn = Button(text="Retour", size_hint_y=None, height=dp(45))
    btn.bind(on_release=lambda x: setattr(manager, "current", ecran_cible))
    return btn


# -----------------------------------------------------------------
# ÉCRAN CONNEXION
# -----------------------------------------------------------------
class ConnexionScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=dp(30), spacing=dp(15))
        layout.add_widget(HeaderLogo())
        layout.add_widget(Label(text="Connexion", font_size=dp(24), bold=True,
                                color=(0.1, 0.1, 0.1, 1), size_hint_y=None, height=dp(40)))
        layout.add_widget(Label(text="E-mail", size_hint_y=None, height=dp(25), color=(0, 0, 0, 1)))
        self.input_email = TextInput(multiline=False, size_hint_y=None, height=dp(45))
        layout.add_widget(self.input_email)
        layout.add_widget(Label(text="Mot de passe", size_hint_y=None, height=dp(25), color=(0, 0, 0, 1)))
        self.input_mdp = TextInput(multiline=False, password=True, size_hint_y=None, height=dp(45))
        layout.add_widget(self.input_mdp)

        bouton = Button(text="Se connecter", size_hint_y=None, height=dp(55),
                        background_color=(0.2, 0.5, 0.8, 1))
        bouton.bind(on_release=self.se_connecter)
        layout.add_widget(bouton)

        btn_creer = Button(text="Créer un compte", size_hint_y=None, height=dp(45))
        btn_creer.bind(on_release=lambda x: setattr(self.manager, "current", "inscription"))
        layout.add_widget(btn_creer)
        layout.add_widget(Label())
        self.add_widget(layout)

    def se_connecter(self, instance):
        email = self.input_email.text.strip()
        mdp = self.input_mdp.text
        if not email or not mdp:
            popup_info("Erreur", "Merci de remplir l'e-mail et le mot de passe.")
            return
        if verifier_utilisateur(email, mdp):
            self.input_email.text = ""
            self.input_mdp.text = ""
            self.manager.get_screen("accueil").definir_utilisateur(email)
            self.manager.current = "accueil"
        else:
            popup_info("Erreur", "E-mail ou mot de passe incorrect.")


# -----------------------------------------------------------------
# ÉCRAN INSCRIPTION
# -----------------------------------------------------------------
class InscriptionScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        outer = BoxLayout(orientation="vertical")
        outer.add_widget(HeaderLogo())
        scroll = ScrollView()
        layout = BoxLayout(orientation="vertical", padding=dp(30), spacing=dp(12), size_hint_y=None)
        layout.bind(minimum_height=layout.setter("height"))

        layout.add_widget(Label(text="Créer un compte", font_size=dp(24), bold=True,
                                color=(0.1, 0.1, 0.1, 1), size_hint_y=None, height=dp(40)))
        champs = [("Nom", "input_nom", False), ("Prénom", "input_prenom", False),
                  ("E-mail", "input_email", False), ("École", "input_ecole", False),
                  ("Mot de passe", "input_mdp", True)]
        for texte, attribut, mdp in champs:
            layout.add_widget(Label(text=texte, size_hint_y=None, height=dp(25), color=(0, 0, 0, 1)))
            champ = TextInput(multiline=False, password=mdp, size_hint_y=None, height=dp(45))
            setattr(self, attribut, champ)
            layout.add_widget(champ)

        bouton = Button(text="Créer mon compte", size_hint_y=None, height=dp(55),
                        background_color=(0.2, 0.6, 0.4, 1))
        bouton.bind(on_release=self.creer_compte)
        layout.add_widget(bouton)

        btn_retour = Button(text="J'ai déjà un compte", size_hint_y=None, height=dp(45))
        btn_retour.bind(on_release=lambda x: setattr(self.manager, "current", "connexion"))
        layout.add_widget(btn_retour)
        layout.add_widget(Label(size_hint_y=None, height=dp(20)))
        scroll.add_widget(layout)
        outer.add_widget(scroll)
        self.add_widget(outer)

    def creer_compte(self, instance):
        nom = self.input_nom.text.strip()
        prenom = self.input_prenom.text.strip()
        email = self.input_email.text.strip()
        ecole = self.input_ecole.text.strip()
        mdp = self.input_mdp.text

        if not nom or not prenom or not email or not mdp:
            popup_info("Erreur", "Merci de remplir tous les champs obligatoires.")
            return
        if "@" not in email:
            popup_info("Erreur", "Adresse e-mail invalide.")
            return

        try:
            succes = creer_utilisateur(nom, prenom, email, ecole, mdp, None, None)
        except Exception as erreur:
            popup_info("Erreur inattendue", str(erreur))
            return

        if not succes:
            popup_info("Erreur", "Un compte existe déjà avec cet e-mail.")
            return

        popup_info("Bienvenue", f"Compte créé pour {prenom} {nom}. Tu peux te connecter.")
        for champ in (self.input_nom, self.input_prenom, self.input_email,
                      self.input_ecole, self.input_mdp):
            champ.text = ""
        self.manager.current = "connexion"


# -----------------------------------------------------------------
# ÉCRAN RÉCUPÉRATION
# -----------------------------------------------------------------
class RecuperationScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.email_en_cours = None
        self.layout = BoxLayout(orientation="vertical")
        self.layout.add_widget(HeaderLogo())
        self.corps = BoxLayout(orientation="vertical", padding=dp(30), spacing=dp(15))
        self.layout.add_widget(self.corps)
        self.add_widget(self.layout)
        self.afficher_etape_email()

    def on_pre_enter(self, *args):
        self.email_en_cours = None
        self.afficher_etape_email()

    def afficher_etape_email(self):
        self.corps.clear_widgets()
        self.corps.add_widget(Label(text="Mot de passe oublié", font_size=dp(22), bold=True,
                                    color=(0.1, 0.1, 0.1, 1), size_hint_y=None, height=dp(35)))
        self.corps.add_widget(Label(text="Entre l'e-mail de ton compte", size_hint_y=None,
                                    height=dp(25), color=(0, 0, 0, 1)))
        self.input_email = TextInput(multiline=False, size_hint_y=None, height=dp(45))
        self.corps.add_widget(self.input_email)
        btn_suivant = Button(text="Suivant", size_hint_y=None, height=dp(55),
                             background_color=(0.2, 0.5, 0.8, 1))
        btn_suivant.bind(on_release=self.verifier_email)
        self.corps.add_widget(btn_suivant)
        self.corps.add_widget(bouton_retour(self.manager, "connexion"))
        self.corps.add_widget(Label())

    def verifier_email(self, *args):
        email = self.input_email.text.strip()
        question = obtenir_question(email)
        if question is None:
            popup_info("Erreur", "Aucun compte trouvé avec cet e-mail.")
            return
        self.email_en_cours = email
        self.afficher_etape_question(question)

    def afficher_etape_question(self, question):
        self.corps.clear_widgets()
        self.corps.add_widget(Label(text=question, size_hint_y=None, height=dp(40), color=(0, 0, 0, 1)))
        self.input_reponse = TextInput(multiline=False, size_hint_y=None, height=dp(45))
        self.corps.add_widget(self.input_reponse)
        btn_verifier = Button(text="Vérifier", size_hint_y=None, height=dp(55),
                              background_color=(0.2, 0.5, 0.8, 1))
        btn_verifier.bind(on_release=self.verifier_reponse_utilisateur)
        self.corps.add_widget(btn_verifier)
        self.corps.add_widget(bouton_retour(self.manager, "connexion"))
        self.corps.add_widget(Label())

    def verifier_reponse_utilisateur(self, *args):
        reponse = self.input_reponse.text.strip()
        if not verifier_reponse(self.email_en_cours, reponse):
            popup_info("Erreur", "Réponse incorrecte.")
            return
        self.afficher_etape_nouveau_mdp()

    def afficher_etape_nouveau_mdp(self):
        self.corps.clear_widgets()
        self.corps.add_widget(Label(text="Nouveau mot de passe", size_hint_y=None,
                                    height=dp(25), color=(0, 0, 0, 1)))
        self.input_nouveau_mdp = TextInput(multiline=False, password=True, size_hint_y=None, height=dp(45))
        self.corps.add_widget(self.input_nouveau_mdp)
        bouton = Button(text="Enregistrer", size_hint_y=None, height=dp(55),
                        background_color=(0.2, 0.6, 0.4, 1))
        bouton.bind(on_release=self.valider_nouveau_mdp)
        self.corps.add_widget(bouton)
        self.corps.add_widget(Label())

    def valider_nouveau_mdp(self, *args):
        nouveau_mdp = self.input_nouveau_mdp.text
        if not nouveau_mdp or len(nouveau_mdp) < 4:
            popup_info("Erreur", "Le mot de passe doit contenir au moins 4 caractères.")
            return
        reinitialiser_mdp(self.email_en_cours, nouveau_mdp)
        popup_info("Succès", "Mot de passe mis à jour. Connecte-toi.")
        self.manager.current = "connexion"


# -----------------------------------------------------------------
# ÉCRAN ACCUEIL
# -----------------------------------------------------------------
class AccueilScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=dp(30), spacing=dp(15))
        layout.add_widget(HeaderLogo())
        self.label_bienvenue = Label(text="Bienvenue !", font_size=dp(22), bold=True,
                                     color=(0.1, 0.1, 0.1, 1), size_hint_y=None, height=dp(40))
        layout.add_widget(self.label_bienvenue)

        boutons = [
            ("🏫 Classes", "classes"),
            ("🧑‍🎓 Élèves", "eleves"),
            ("📚 Matières", "matieres"),
            ("📝 Notes & bulletins", "eleves_pour_notes"),
        ]
        for texte, cible in boutons:
            btn = Button(text=texte, size_hint_y=None, height=dp(50), background_color=(0.2, 0.5, 0.8, 1))
            btn.bind(on_release=lambda x, c=cible: setattr(self.manager, "current", c))
            layout.add_widget(btn)

        layout.add_widget(Label())
        btn_deconnexion = Button(text="🚪 Se déconnecter", size_hint_y=None, height=dp(45),
                                 background_color=(0.6, 0.3, 0.3, 1))
        btn_deconnexion.bind(on_release=lambda x: setattr(self.manager, "current", "connexion"))
        layout.add_widget(btn_deconnexion)
        self.add_widget(layout)

    def definir_utilisateur(self, email):
        self.label_bienvenue.text = f"Bienvenue, {obtenir_prenom(email)} !"


# -----------------------------------------------------------------
# ÉCRAN CLASSES
# -----------------------------------------------------------------
class ClassesScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical")
        self.layout.add_widget(HeaderLogo("Classes"))

        ajout = BoxLayout(size_hint_y=None, height=dp(50), padding=dp(5), spacing=dp(5))
        self.input_nom = TextInput(hint_text="Nom de la classe (ex: CM2)", multiline=False)
        btn_ajout = Button(text="Ajouter", size_hint_x=None, width=dp(90),
                           background_color=(0.2, 0.6, 0.4, 1))
        btn_ajout.bind(on_release=self.ajouter)
        ajout.add_widget(self.input_nom)
        ajout.add_widget(btn_ajout)
        self.layout.add_widget(ajout)

        self.scroll = ScrollView()
        self.grid = GridLayout(cols=1, size_hint_y=None, spacing=dp(6), padding=dp(10))
        self.grid.bind(minimum_height=self.grid.setter("height"))
        self.scroll.add_widget(self.grid)
        self.layout.add_widget(self.scroll)
        self.layout.add_widget(bouton_retour(self.manager, "accueil"))
        self.add_widget(self.layout)

    def on_pre_enter(self, *args):
        self.rafraichir()

    def ajouter(self, *args):
        nom = self.input_nom.text.strip()
        if not nom:
            popup_info("Erreur", "Le nom de la classe est obligatoire.")
            return
        if not ajouter_classe(nom):
            popup_info("Erreur", "Cette classe existe déjà.")
            return
        self.input_nom.text = ""
        self.rafraichir()

    def rafraichir(self):
        self.grid.clear_widgets()
        classes = liste_classes()
        if not classes:
            self.grid.add_widget(Label(text="Aucune classe.", size_hint_y=None, height=dp(35),
                                       color=(0.3, 0.3, 0.3, 1)))
        for classe_id, nom in classes:
            ligne = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(5))
            ligne.add_widget(Label(text=nom, color=(0, 0, 0, 1)))
            btn = Button(text="Suppr.", size_hint_x=None, width=dp(80), background_color=(0.8, 0.3, 0.3, 1))
            btn.bind(on_release=lambda x, cid=classe_id: self.supprimer(cid))
            ligne.add_widget(btn)
            self.grid.add_widget(ligne)

    def supprimer(self, classe_id):
        supprimer_classe(classe_id)
        self.rafraichir()


# -----------------------------------------------------------------
# ÉCRAN MATIÈRES
# -----------------------------------------------------------------
class MatieresScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical")
        self.layout.add_widget(HeaderLogo("Matières"))

        ajout = BoxLayout(size_hint_y=None, height=dp(50), padding=dp(5), spacing=dp(5))
        self.input_nom = TextInput(hint_text="Matière (ex: Maths)", multiline=False)
        self.input_coeff = TextInput(hint_text="Coeff.", multiline=False, input_filter="float",
                                     size_hint_x=None, width=dp(70))
        btn_ajout = Button(text="Ajouter", size_hint_x=None, width=dp(90),
                           background_color=(0.2, 0.6, 0.4, 1))
        btn_ajout.bind(on_release=self.ajouter)
        ajout.add_widget(self.input_nom)
        ajout.add_widget(self.input_coeff)
        ajout.add_widget(btn_ajout)
        self.layout.add_widget(ajout)

        self.scroll = ScrollView()
        self.grid = GridLayout(cols=1, size_hint_y=None, spacing=dp(6), padding=dp(10))
        self.grid.bind(minimum_height=self.grid.setter("height"))
        self.scroll.add_widget(self.grid)
        self.layout.add_widget(self.scroll)
        self.layout.add_widget(bouton_retour(self.manager, "accueil"))
        self.add_widget(self.layout)

    def on_pre_enter(self, *args):
        self.rafraichir()

    def ajouter(self, *args):
        nom = self.input_nom.text.strip()
        coeff_texte = self.input_coeff.text.strip()
        if not nom or not coeff_texte:
            popup_info("Erreur", "Renseigne la matière et le coefficient.")
            return
        if not ajouter_matiere(nom, float(coeff_texte)):
            popup_info("Erreur", "Cette matière existe déjà.")
            return
        self.input_nom.text = ""
        self.input_coeff.text = ""
        self.rafraichir()

    def rafraichir(self):
        self.grid.clear_widgets()
        matieres = liste_matieres()
        if not matieres:
            self.grid.add_widget(Label(text="Aucune matière.", size_hint_y=None, height=dp(35),
                                       color=(0.3, 0.3, 0.3, 1)))
        for matiere_id, nom, coeff in matieres:
            ligne = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(5))
            ligne.add_widget(Label(text=f"{nom} (coeff. {coeff:g})", color=(0, 0, 0, 1)))
            btn = Button(text="Suppr.", size_hint_x=None, width=dp(80), background_color=(0.8, 0.3, 0.3, 1))
            btn.bind(on_release=lambda x, mid=matiere_id: self.supprimer(mid))
            ligne.add_widget(btn)
            self.grid.add_widget(ligne)

    def supprimer(self, matiere_id):
        supprimer_matiere(matiere_id)
        self.rafraichir()


# -----------------------------------------------------------------
# POPUP CHOIX PHOTO
# -----------------------------------------------------------------
def choisir_photo(callback):
    layout = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))
    chooser = FileChooserIconView(path="/storage/emulated/0/", filters=["*.png", "*.jpg", "*.jpeg"])
    layout.add_widget(chooser)

    ligne_boutons = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
    btn_choisir = Button(text="Choisir")
    btn_annuler = Button(text="Annuler")
    ligne_boutons.add_widget(btn_choisir)
    ligne_boutons.add_widget(btn_annuler)
    layout.add_widget(ligne_boutons)

    popup = Popup(title="Choisir une photo", content=layout, size_hint=(0.95, 0.95))

    def valider(*args):
        if chooser.selection:
            callback(chooser.selection[0])
        popup.dismiss()

    btn_choisir.bind(on_release=valider)
    btn_annuler.bind(on_release=lambda x: popup.dismiss())
    popup.open()


# -----------------------------------------------------------------
# ÉCRAN AJOUT ÉLÈVE
# -----------------------------------------------------------------
class EleveAjoutScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.chemin_photo_choisie = None

        outer = BoxLayout(orientation="vertical")
        outer.add_widget(HeaderLogo("Ajouter un élève"))
        layout = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(12))

        layout.add_widget(Label(text="Nom", size_hint_y=None, height=dp(25), color=(0, 0, 0, 1)))
        self.input_nom = TextInput(multiline=False, size_hint_y=None, height=dp(45))
        layout.add_widget(self.input_nom)

        layout.add_widget(Label(text="Prénom", size_hint_y=None, height=dp(25), color=(0, 0, 0, 1)))
        self.input_prenom = TextInput(multiline=False, size_hint_y=None, height=dp(45))
        layout.add_widget(self.input_prenom)

        layout.add_widget(Label(text="Classe", size_hint_y=None, height=dp(25), color=(0, 0, 0, 1)))
        self.spinner_classe = Spinner(text="Choisir une classe", values=[], size_hint_y=None, height=dp(45))
        layout.add_widget(self.spinner_classe)

        self.apercu_photo = Image(size_hint_y=None, height=dp(100))
        layout.add_widget(self.apercu_photo)

        btn_photo = Button(text="📷 Choisir une photo", size_hint_y=None, height=dp(45))
        btn_photo.bind(on_release=lambda x: choisir_photo(self.photo_choisie))
        layout.add_widget(btn_photo)

        btn_valider = Button(text="Enregistrer l'élève", size_hint_y=None, height=dp(55),
                             background_color=(0.2, 0.6, 0.4, 1))
        btn_valider.bind(on_release=self.enregistrer)
        layout.add_widget(btn_valider)

        self.zone_retour = BoxLayout(size_hint_y=None, height=dp(45))
        layout.add_widget(self.zone_retour)
        outer.add_widget(layout)
        self.add_widget(outer)

    def on_pre_enter(self, *args):
        self.spinner_classe.values = [nom for _, nom in liste_classes()]
        self.zone_retour.clear_widgets()
        self.zone_retour.add_widget(bouton_retour(self.manager, "eleves"))

    def photo_choisie(self, chemin):
        self.chemin_photo_choisie = chemin
        self.apercu_photo.source = chemin
        self.apercu_photo.reload()

    def enregistrer(self, *args):
        nom = self.input_nom.text.strip()
        prenom = self.input_prenom.text.strip()
        classe_nom = self.spinner_classe.text

        if not nom or not prenom:
            popup_info("Erreur", "Le nom et le prénom sont obligatoires.")
            return
        if classe_nom == "Choisir une classe":
            popup_info("Erreur", "Merci de choisir une classe (ou d'en créer une d'abord).")
            return

        classe_id = None
        for cid, cnom in liste_classes():
            if cnom == classe_nom:
                classe_id = cid
                break

        photo_finale = None
        if self.chemin_photo_choisie:
            nom_fichier = f"{nom}_{prenom}_{os.path.basename(self.chemin_photo_choisie)}"
            destination = os.path.join(DOSSIER_PHOTOS, nom_fichier)
            try:
                shutil.copy(self.chemin_photo_choisie, destination)
                photo_finale = destination
            except Exception:
                photo_finale = None

        ajouter_eleve(nom, prenom, classe_id, photo_finale)
        popup_info("Succès", f"{prenom} {nom} a été ajouté(e).")
        self.input_nom.text = ""
        self.input_prenom.text = ""
        self.chemin_photo_choisie = None
        self.apercu_photo.source = ""
        self.manager.current = "eleves"


# -----------------------------------------------------------------
# ÉCRAN LISTE ÉLÈVES
# -----------------------------------------------------------------
class ElevesScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical")
        self.layout.add_widget(HeaderLogo("Élèves"))

        btn_ajout = Button(text="➕ Ajouter un élève", size_hint_y=None, height=dp(50),
                           background_color=(0.2, 0.6, 0.4, 1))
        btn_ajout.bind(on_release=lambda x: setattr(self.manager, "current", "eleve_ajout"))
        self.layout.add_widget(btn_ajout)

        self.scroll = ScrollView()
        self.grid = GridLayout(cols=1, size_hint_y=None, spacing=dp(8), padding=dp(10))
        self.grid.bind(minimum_height=self.grid.setter("height"))
        self.scroll.add_widget(self.grid)
        self.layout.add_widget(self.scroll)
        self.layout.add_widget(bouton_retour(self.manager, "accueil"))
        self.add_widget(self.layout)

    def on_pre_enter(self, *args):
        self.rafraichir()

    def rafraichir(self):
        self.grid.clear_widgets()
        eleves = liste_eleves()
        if not eleves:
            self.grid.add_widget(Label(text="Aucun élève.", size_hint_y=None, height=dp(35),
                                       color=(0.3, 0.3, 0.3, 1)))
        for eleve_id, nom, prenom, classe_nom, photo in eleves:
            ligne = BoxLayout(size_hint_y=None, height=dp(65), spacing=dp(8))
            if photo and os.path.exists(photo):
                ligne.add_widget(Image(source=photo, size_hint=(None, None), size=(dp(50), dp(50))))
            else:
                ligne.add_widget(Label(text="👤", font_size=dp(28), size_hint=(None, None), size=(dp(50), dp(50))))
            ligne.add_widget(Label(text=f"{prenom} {nom} ({classe_nom or '-'})", color=(0, 0, 0, 1)))
            btn = Button(text="Suppr.", size_hint_x=None, width=dp(80), background_color=(0.8, 0.3, 0.3, 1))
            btn.bind(on_release=lambda x, eid=eleve_id: self.supprimer(eid))
            ligne.add_widget(btn)
            self.grid.add_widget(ligne)

    def supprimer(self, eleve_id):
        supprimer_eleve(eleve_id)
        self.rafraichir()


# -----------------------------------------------------------------
# ÉCRAN CHOIX ÉLÈVE POUR NOTES
# -----------------------------------------------------------------
class ElevesPourNotesScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical")
        self.layout.add_widget(HeaderLogo("Choisir un élève"))
        self.scroll = ScrollView()
        self.grid = GridLayout(cols=1, size_hint_y=None, spacing=dp(6), padding=dp(10))
        self.grid.bind(minimum_height=self.grid.setter("height"))
        self.scroll.add_widget(self.grid)
        self.layout.add_widget(self.scroll)
        self.layout.add_widget(bouton_retour(self.manager, "accueil"))
        self.add_widget(self.layout)

    def on_pre_enter(self, *args):
        self.grid.clear_widgets()
        eleves = liste_eleves()
        if not eleves:
            self.grid.add_widget(Label(text="Aucun élève. Ajoute-en un d'abord.", size_hint_y=None,
                                       height=dp(35), color=(0.3, 0.3, 0.3, 1)))
        for eleve_id, nom, prenom, classe_nom, photo in eleves:
            btn = Button(text=f"{prenom} {nom} ({classe_nom or '-'})", size_hint_y=None, height=dp(50),
                        background_color=(0.2, 0.5, 0.8, 1))
            btn.bind(on_release=lambda x, eid=eleve_id, n=nom, p=prenom: self.choisir(eid, n, p))
            self.grid.add_widget(btn)

    def choisir(self, eleve_id, nom, prenom):
        ecran = self.manager.get_screen("bulletin")
        ecran.charger(eleve_id, nom, prenom)
        self.manager.current = "bulletin"


# -----------------------------------------------------------------
# ÉCRAN BULLETIN (notes + appréciation + moyenne)
# -----------------------------------------------------------------
class BulletinScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.eleve_id = None
        self.trimestre = TRIMESTRES[0]
        self.champs_notes = {}

        self.layout = BoxLayout(orientation="vertical")
        self.header = HeaderLogo("Bulletin")
        self.layout.add_widget(self.header)

        self.spinner_trimestre = Spinner(text=TRIMESTRES[0], values=TRIMESTRES,
                                         size_hint_y=None, height=dp(45))
        self.spinner_trimestre.bind(text=self.changer_trimestre)
        self.layout.add_widget(self.spinner_trimestre)

        self.scroll = ScrollView()
        self.grid = GridLayout(cols=1, size_hint_y=None, spacing=dp(8), padding=dp(10))
        self.grid.bind(minimum_height=self.grid.setter("height"))
        self.scroll.add_widget(self.grid)
        self.layout.add_widget(self.scroll)

        self.label_moyenne = Label(text="Moyenne : -", bold=True, size_hint_y=None, height=dp(35),
                                   color=(0.1, 0.4, 0.1, 1))
        self.layout.add_widget(self.label_moyenne)

        self.layout.add_widget(Label(text="Appréciation", size_hint_y=None, height=dp(25), color=(0, 0, 0, 1)))
        self.input_appreciation = TextInput(multiline=True, size_hint_y=None, height=dp(80))
        self.layout.add_widget(self.input_appreciation)

        btn_enregistrer = Button(text="Enregistrer", size_hint_y=None, height=dp(50),
                                 background_color=(0.2, 0.6, 0.4, 1))
        btn_enregistrer.bind(on_release=self.enregistrer_tout)
        self.layout.add_widget(btn_enregistrer)

        self.zone_retour = BoxLayout(size_hint_y=None, height=dp(45))
        self.layout.add_widget(self.zone_retour)
        self.add_widget(self.layout)

    def charger(self, eleve_id, nom, prenom):
        self.eleve_id = eleve_id
        for widget in list(self.header.children):
            self.header.remove_widget(widget)
        if os.path.exists(LOGO_PATH):
            self.header.add_widget(Image(source=LOGO_PATH, size_hint=(None, None), size=(dp(60), dp(60)),
                                         pos_hint={"center_x": 0.5}))
        self.header.add_widget(Label(text=f"Bulletin de {prenom} {nom}", font_size=dp(18), bold=True,
                                     color=(0.1, 0.1, 0.1, 1), size_hint_y=None, height=dp(30)))
        self.zone_retour.clear_widgets()
        self.zone_retour.add_widget(bouton_retour(self.manager, "eleves_pour_notes"))
        self.spinner_trimestre.text = TRIMESTRES[0]
        self.trimestre = TRIMESTRES[0]
        self.rafraichir()

    def changer_trimestre(self, spinner, texte):
        self.trimestre = texte
        self.rafraichir()

    def rafraichir(self):
        self.grid.clear_widgets()
        self.champs_notes = {}
        matieres = notes_eleve_trimestre(self.eleve_id, self.trimestre)
        if not matieres:
            self.grid.add_widget(Label(text="Aucune matière créée. Ajoute des matières d'abord.",
                                       size_hint_y=None, height=dp(40), color=(0.3, 0.3, 0.3, 1)))
        for matiere_id, nom, coeff, note in matieres:
            ligne = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
            ligne.add_widget(Label(text=f"{nom} (coeff. {coeff:g})", color=(0, 0, 0, 1)))
            champ = TextInput(text=str(note) if note is not None else "", multiline=False,
                              input_filter="float", size_hint_x=None, width=dp(70))
            self.champs_notes[matiere_id] = champ
            ligne.add_widget(champ)
            self.grid.add_widget(ligne)

        moyenne = calculer_moyenne(self.eleve_id, self.trimestre)
        self.label_moyenne.text = f"Moyenne : {moyenne:.2f}/20" if moyenne is not None else "Moyenne : -"
        self.input_appreciation.text = obtenir_appreciation(self.eleve_id, self.trimestre)

    def enregistrer_tout(self, *args):
        for matiere_id, champ in self.champs_notes.items():
            texte = champ.text.strip()
            if texte:
                enregistrer_note(self.eleve_id, matiere_id, self.trimestre, float(texte))
        enregistrer_appreciation(self.eleve_id, self.trimestre, self.input_appreciation.text.strip())
        popup_info("Succès", "Notes et appréciation enregistrées.")
        self.rafraichir()


# -----------------------------------------------------------------
# APPLICATION
# -----------------------------------------------------------------
class MonApplication(App):
    def build(self):
        self.title = "Gestion Scolaire"
        init_db()
        sm = ScreenManager()
        sm.add_widget(ConnexionScreen(name="connexion"))
        sm.add_widget(InscriptionScreen(name="inscription"))
        sm.add_widget(RecuperationScreen(name="recuperation"))
        sm.add_widget(AccueilScreen(name="accueil"))
        sm.add_widget(ClassesScreen(name="classes"))
        sm.add_widget(MatieresScreen(name="matieres"))
        sm.add_widget(ElevesScreen(name="eleves"))
        sm.add_widget(EleveAjoutScreen(name="eleve_ajout"))
        sm.add_widget(ElevesPourNotesScreen(name="eleves_pour_notes"))
        sm.add_widget(BulletinScreen(name="bulletin"))
        return sm


if __name__ == "__main__":
    MonApplication().run()
