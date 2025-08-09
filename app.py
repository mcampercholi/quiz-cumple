from flask import Flask, render_template, request, redirect, session, url_for
from preguntas import questions, target_score
import os

app = Flask(__name__)
app.secret_key = 'super-secreto-temporal'

print(">>> app.py se está ejecutando")
print(__name__)

@app.route('/')
def landing():
    print("Se ejecutó landing()")
    session.clear()
    return render_template('landing.html')

@app.route('/reset')
def reset():
    session.clear()
    return redirect(url_for('landing'))

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if 'q_index' not in session:
        session['q_index'] = 0
        session['score'] = 0
        session['last_correct'] = None
        session['user_answer'] = ""

    q_index = session['q_index']

    if q_index >= len(questions):
        if session['score'] >= target_score:
            return redirect(url_for('meta'))
        else:
            return redirect(url_for('result'))

    question = questions[q_index]

    if request.method == 'POST':
        user_answer = request.form.get('answer', '').strip()
        is_correct = user_answer.lower() == question['answer'].strip().lower()

        session['last_correct'] = is_correct
        session['user_answer'] = user_answer  # original para mostrar

        if is_correct:
            session['score'] += question['weight']    
        else:
            session['score'] -= question['weight']

        return render_template(
            'quiz.html',
            question=question,
            score=session['score'],
            target=target_score,
            last_correct=is_correct,
            show_feedback=True,
            user_answer=user_answer
        )

    # GET después del feedback → avanzar
    if session.get('last_correct') is not None:
        session['q_index'] += 1
        session['last_correct'] = None
        session['user_answer'] = ""
        return redirect(url_for('quiz'))

    return render_template(
        'quiz.html',
        question=question,
        score=session['score'],
        target=target_score,
        last_correct=None,
        show_feedback=False
    )





@app.route('/result')
def result():
    return render_template('result.html', score=session['score'], target=target_score)

@app.route('/meta')
def meta():
    return render_template('meta.html', score=session['score'])

if __name__ == '__main__':
    app.run(debug=True)
