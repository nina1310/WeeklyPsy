from flask import Flask, render_template, request, redirect, url_for
import json, os, hashlib, random
from datetime import datetime

app = Flask(__name__)
USER_FILE = 'users.json'

def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

@app.route('/')
def home():
    return redirect(url_for('accueil'))

@app.route('/accueil')
def accueil():
    return render_template("accueil.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        pseudo = request.form['username']
        password = request.form['password']
        users = load_users()

        if pseudo in users:
            hashed = hashlib.sha256(password.encode()).hexdigest()
            if users[pseudo]["password"] == hashed:
                return redirect(url_for('dashboard', pseudo=pseudo))
            else:
                return render_template("connexion.html", error="Mot de passe incorrect.")
        else:
            return render_template("connexion.html", error="Ce pseudo n'existe pas.")

    return render_template("connexion.html")


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        print("Formulaire reçu :", request.form)
        pseudo = request.form.get('username')
        password = request.form.get('password')

        if not pseudo or not password:
            return render_template("creer_compte.html", error="Tous les champs sont requis.")

        users = load_users()

        if pseudo in users:
            return render_template("creer_compte.html", error="Pseudo déjà utilisé.")

        hashed = hashlib.sha256(password.encode()).hexdigest()
        users[pseudo] = {"password": hashed, "reponses": []}
        save_users(users)
        print("✅ Compte créé pour :", pseudo)
        return redirect(url_for('login'))

    return render_template("creer_compte.html")


@app.route('/dashboard/<pseudo>')
def dashboard(pseudo):
    users = load_users()
    if pseudo in users:
        return render_template("dashboard.html", pseudo=pseudo, reponses=users[pseudo].get('reponses', []))
    return redirect(url_for('login'))

@app.route('/suivi/<pseudo>', methods=['GET', 'POST'])
def suivi(pseudo):
    users = load_users()
    if pseudo not in users:
        return redirect(url_for('login'))

    today = datetime.now().strftime("%Y-%m-%d")

    # Vérifie si un suivi a été fait aujourd'hui
    for rep in users[pseudo]["reponses"]:
        if rep["date"] == today:
            if "motivation" in rep and "avancement" in rep:
                # Suivi émotionnel + études déjà remplis
                return render_template("dashboard.html", pseudo=pseudo, reponses=users[pseudo]["reponses"], message="Tu as déjà rempli ton suivi aujourd’hui 😉")
            else:
                # Suivi émotionnel fait mais pas les études
                return redirect(url_for('suivi_etudes', pseudo=pseudo))

    # Reset après 7 jours
    if len(users[pseudo]["reponses"]) >= 7:
        users[pseudo]["reponses"] = []
        users[pseudo]["questions_posées"] = []

    # Tirage d'une question spéciale non répétée
    all_questions = [
        "As-tu ressenti de la solitude aujourd’hui ?",
        "As-tu reçu du soutien aujourd’hui ?",
        "As-tu ri aujourd’hui ?",
        "As-tu été fier(e) de toi aujourd’hui ?",
        "As-tu partagé un moment agréable ?",
        "As-tu ressenti de la motivation ?",
        "As-tu ressenti de la fatigue émotionnelle ?"
    ]
    deja_posees = users[pseudo].get("questions_posées", [])
    restantes = [q for q in all_questions if q not in deja_posees]

    if not restantes:
        restantes = all_questions
        deja_posees = []
    
    question_du_jour = random.choice(restantes)



    if request.method == 'POST':
        emotions = request.form.getlist('emotions')
        triste = request.form.get('triste')
        colere = request.form.get('colere')
        stress = int(request.form.get('stress', 5))
        etudes = int(request.form.get('etudes', 5))
        extra = request.form.get('extra', 'non')

        reponse_du_jour = {
            "date": today,
            "emotions": emotions,
            "triste": triste,
            "colere": colere,
            "stress": stress,
            "etudes": etudes,
            "question_speciale": question_du_jour,
            "reponse_speciale": extra
        }

        users[pseudo]["reponses"].append(reponse_du_jour)
        deja_posees.append(question_du_jour)
        users[pseudo]["questions_posées"] = deja_posees
        save_users(users)
        return redirect(url_for('suivi_etudes', pseudo=pseudo))

    return render_template("suivi.html", pseudo=pseudo, question_speciale=question_du_jour)



@app.route('/suivi_etudes/<pseudo>', methods=['GET', 'POST'])
def suivi_etudes(pseudo):
    users = load_users()
    if pseudo not in users:
        return redirect(url_for('login'))

    if request.method == 'POST':
        if not users[pseudo]["reponses"]:
            return redirect(url_for('dashboard', pseudo=pseudo))

        reponse_du_jour = users[pseudo]["reponses"][-1]

        reponse_du_jour["concentration"] = int(request.form.get('concentration', 5))
        reponse_du_jour["motivation"] = int(request.form.get('motivation', 5))
        reponse_du_jour["avancement"] = request.form.get('avancement')
        reponse_du_jour["envie_arret"] = request.form.get('envie_arret')
        reponse_du_jour["retard"] = request.form.get('retard')
        reponse_du_jour["incomprehension"] = request.form.get('incomprehension')

        save_users(users)
        return redirect(url_for('dashboard', pseudo=pseudo))

    return render_template("suivi_etudes.html", pseudo=pseudo)

@app.route('/bilan/<pseudo>')
def bilan(pseudo):
    users = load_users()
    if pseudo not in users:
        return redirect(url_for('login'))

    reponses = users[pseudo].get("reponses", [])
    nb_reponses = len(reponses)

    if nb_reponses == 0:
        return f"Aucune réponse enregistrée pour {pseudo}"

    compteur = {
        "triste": 0, "colere": 0, "stress": [], "etudes": [],
        "joie": 0, "gratitude": 0, "jalousie": 0, "fierté": 0,
        "anxiété": 0, "culpabilité": 0
    }

    for rep in reponses:
        emotions = rep.get("emotions", [])
        for e in emotions:
            if e in compteur:
                compteur[e] += 1

        if rep.get("colere") == "oui":
            compteur["colere"] += 2
        elif rep.get("colere") == "un peu":
            compteur["colere"] += 1

        compteur["stress"].append(rep.get("stress", 5))
        compteur["etudes"].append(rep.get("etudes", 5))

    resume = []

    if nb_reponses < 7:
        resume.append(f"Voici un petit retour sur ta journée :")

        if compteur["triste"] >= 2:
            resume.append("Tu as été triste, n'oublie pas qu'après la pluie vient l'arc-en-ciel :) Tu peux lire un livre ou regarder une série ce soir pour te changer les idées.")
        if compteur["colere"] >= 2:
            resume.append("Ta colère a sûrement été légitime. Essaie de penser à autre chose et balaye cette histoire du revers de la main, tu mérites d'être en paix.")
        if compteur["stress"] and sum(compteur["stress"]) / len(compteur["stress"]) > 6:
            resume.append("Tu es stressé(e), n'oublie pas de prendre un moment de méditation avant de dormir. (PS : ça n'en vaut pas la peine) ")
        if compteur["etudes"] and sum(compteur["etudes"]) / len(compteur["etudes"]) < 5:
            resume.append("Les cours ont été difficiles aujourd'hui... Prends le temps qu'il faut pour reprendre chaque notion et n'hésite pas à demander de l'aide pour que ça aille mieux demain ;)")
        if compteur["culpabilité"] >= 2:
            resume.append("La culpabilité s’est montrée souvent. Tu fais de ton mieux, c’est ce qui compte.")
        if compteur["joie"] >= 2:
            resume.append("Tu es joyeux(se) en ce moment ! Garde ce beau sourire.")

        if not any(r.startswith("Tu ") for r in resume):
            resume.append("Pour l’instant, cette semaine se montre plutôt agréable ! Je suis fière de toi.")

    else:
        resume.append("Bravo ! Tu as complété une semaine entière de suivi 🏁")
        resume.append("Voici ton bilan complet. Prends un moment pour le lire attentivement, tu le mérites.")

        if compteur["triste"] >= 4:
            resume.append("Tu as semblé traverser une période de tristesse. Si un événement t’a touché(e), c’est normal de te sentir comme ça. Autorise-toi à pleurer, cela fait du bien. Mais si ce chagrin prend trop de place dans ta vie, n'hésite pas à en parler à quelqu’un. La psychologue de l’Université reçoit avec ou sans rendez-vous, tu trouveras ses horaires sur l’Instagram de l’Université. Tu peux aussi essayer le journaling, cela peut vraiment aider à poser ses émotions. Courage, tout va finir par s’éclaircir 🌈")

        if compteur["colere"] >= 4:
            resume.append("Tu as été particulièrement en colère. Si cela est dû à certains conflits à l’Université, tu peux te tourner vers Monsieur Delbot, le médiateur. Il est là pour aider, et il est vraiment bienveillant. Sinon, certaines activités physiques comme la boxe ou la course peuvent aider à canaliser cette énergie.")

        if sum(compteur["stress"]) / len(compteur["stress"]) > 6:
            resume.append("Tu as été très stressé(e) ces derniers jours. C’est compréhensible quand on jongle avec plein de responsabilités. Mais rappelle-toi : rien ne vaut ta tranquillité d’esprit. Tu pourrais essayer de prendre 10 minutes pour respirer, méditer, ou faire un peu de yoga avant de dormir. Ton corps et ton esprit ont besoin de repos aussi 💆‍♀️")

        if sum(compteur["etudes"]) / len(compteur["etudes"]) < 5:
            resume.append("Tu n’es pas vraiment épanoui(e) dans tes études. C’est peut-être juste une période, ou peut-être que tu te poses des questions plus profondes. Il existe de nombreux parcours différents, et tu pourrais très bien trouver celui qui te correspond. Le Service d’accompagnement à l’orientation (SUIO), au bâtiment Ramnoux, peut t’aider à y voir plus clair.")

        if compteur["joie"] >= 3:
            resume.append("Tu as ressenti beaucoup de joie cette semaine. Prends un instant pour te souvenir de ce qui t’a rendu heureux(se) ;)")

        if compteur["gratitude"] >= 3:
            resume.append("Tu as souvent ressenti de la gratitude. C’est une qualité précieuse : elle nourrit ton bien-être et renforce tes liens aux autres.")

        if compteur["jalousie"] >= 3:
            resume.append("Tu as ressenti de la jalousie à plusieurs reprises. Essaie d’en faire un signal : de quoi aurais-tu envie ou besoin toi aussi ? Écoute-toi, sans jugement. N'oublie pas que tu possèdes en toi beaucoup de qualités uniques.")

        if compteur["fierté"] >= 3:
            resume.append("Tu t’es senti(e) fier(e) de toi cette semaine. C’est super important ! Note ce que tu as accompli pour t’en souvenir plus tard.")

        if compteur["anxiété"] >= 3:
            resume.append("L’anxiété semble avoir été bien présente. Tu n’es pas seul(e) : essaie d'en parler ou de trouver un petit rituel apaisant. Respirer, écrire ou marcher peuvent aider.")

        if compteur["culpabilité"] >= 3:
            resume.append("Tu as souvent ressenti de la culpabilité. Tu fais de ton mieux. Prends soin de ton discours intérieur : sois aussi doux(ce) avec toi que tu le serais avec un(e) ami(e).")

    labels = []
    scores_bonheur = []
    emojis = []

    for rep in reponses:
        date = rep['date']
        emotions = rep.get("emotions", [])
        score = 10

        if "triste" in emotions:
            score -= 2
        if rep.get("colere") == "oui":
            score -= 2
        elif rep.get("colere") == "un peu":
            score -= 1

        score -= (rep.get("stress", 5) - 5) * 0.5
        score += (rep.get("etudes", 5) - 5) * 0.5

        if "joie" in emotions:
            score += 1
        if "gratitude" in emotions:
            score += 1
        if "fierté" in emotions:
            score += 0.5
        if "jalousie" in emotions:
            score -= 1
        if "anxiété" in emotions:
            score -= 1
        if "culpabilité" in emotions:
            score -= 1

        score = max(0, min(10, score))

        if score >= 8:
            emoji = "😄"
        elif score >= 6:
            emoji = "🙂"
        elif score >= 4:
            emoji = "😐"
        elif score >= 2:
            emoji = "😟"
        else:
            emoji = "😢"

        labels.append(date)
        scores_bonheur.append(round(score, 2))
        emojis.append(emoji)

    emoji_dates = list(zip(labels, emojis))

    return render_template(
        "bilan.html",
        pseudo=pseudo,
        resume=resume,
        labels=labels,
        scores_bonheur=scores_bonheur,
        emoji_dates=emoji_dates
    )


@app.route('/logout')
def logout():
 return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

