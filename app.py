from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from preguntas import questions, target_score, max_lives
import os
import unicodedata

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')

print(">>> app.py se está ejecutando")
print(__name__)

# -------- Utils --------
def norm(s):
    """Normaliza para comparar: trim, lower, sin acentos."""
    s = str(s or '').strip().lower()
    s = unicodedata.normalize('NFD', s)
    return ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn')

# -------- Rutas base --------
@app.route('/')
def landing():
    session.clear()
    return render_template('landing.html')

@app.route('/reset')
def reset():
    session.clear()
    return redirect(url_for('landing'))

# -------- Quiz (carga inicial) --------
@app.route('/quiz', methods=['GET'])
def quiz():
    # Inicialización de estado
    if 'q_index' not in session:
        session['q_index'] = 0
        session['score'] = 0
        session['lives'] = int(max_lives)  # <-- usa preguntas.max_lives
        session['last_correct'] = None
        session['awaiting_next'] = False

    # ¿Fin del cuestionario?
    if session['q_index'] >= len(questions):
        if session['score'] >= target_score:
            return redirect(url_for('meta'))
        else:
            return redirect(url_for('result'))

    q = questions[session['q_index']]
    return render_template(
        'quiz.html',
        question=q,
        score=session['score'],
        target=target_score,
        lives=session['lives']
    )

# -------- AJAX: evaluar respuesta SIN recargar --------
@app.route('/answer_ajax', methods=['POST'])
def answer_ajax():
    if 'q_index' not in session:
        return jsonify(error='no_session'), 400

    # Si ya terminó, avisamos
    if session['q_index'] >= len(questions):
        return jsonify(done=True), 200

    q = questions[session['q_index']]
    user_raw = request.form.get('answer')
    is_correct = (norm(user_raw) == norm(q['answer']))

    # Peso positivo por las dudas
    w = abs(int(q.get('weight', 1)))

    if is_correct:
        session['score'] += w
        session['last_correct'] = True
    else:
        # Restar vida (no tocar score en este modelo)
        session['lives'] = max(0, int(session.get('lives', max_lives)) - 1)
        session['last_correct'] = False
        # Game over inmediato si sin vidas
        if session['lives'] == 0:
            return jsonify(
                ok=True,
                correct=False,
                correct_answer=q['answer'],
                user_answer=user_raw,
                score=int(session['score']),
                target=int(target_score),
                lives=int(session['lives']),
                game_over=True
            ), 200

    # Queda en feedback esperando "Siguiente"
    session['awaiting_next'] = True

    return jsonify(
        ok=True,
        correct=bool(is_correct),
        correct_answer=q['answer'],
        user_answer=user_raw,
        score=int(session['score']),
        target=int(target_score),
        lives=int(session['lives']),
        game_over=False
    ), 200

# -------- AJAX: pasar a la siguiente pregunta SIN recargar --------
@app.route('/next_ajax', methods=['POST'])
def next_ajax():
    if 'q_index' not in session:
        return jsonify(error='no_session'), 400

    # Avanzar si veníamos del feedback
    if session.get('awaiting_next'):
        session['awaiting_next'] = False
        session['q_index'] += 1

    # ¿Fin del cuestionario?
    if session['q_index'] >= len(questions):
        return jsonify(
            done=True,
            reached_target=(session['score'] >= target_score),
            score=int(session['score']),
            target=int(target_score),
            lives=int(session['lives'])
        ), 200

    q = questions[session['q_index']]
    return jsonify(
        done=False,
        question={
            "type": q['type'],
            "text": q['text'],
            "options": q.get('options', [])
        },
        score=int(session['score']),
        target=int(target_score),
        lives=int(session['lives'])
    ), 200

# -------- Resultados --------
@app.route('/result')
def result():
    return render_template('result.html', score=session['score'], target=target_score)

@app.route('/meta')
def meta():
    return render_template('meta.html', score=session['score'])

if __name__ == '__main__':
    app.run(debug=True)
