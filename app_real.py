from flask import Flask, render_template, request, redirect, session, url_for
from preguntas import questions, target_score
import os

app = Flask(__name__)
app.secret_key = 'super-secreto-temporal'

print(">>> app.py se está ejecutando")
print(__name__)

@app.route('/')
def landing():
    return render_template('landing.html')


@app.route('/reset')
def reset():
    session.clear()
    return redirect(url_for('landing'))


@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if 'score' not in session:
        session['score'] = 0
        session['q_index'] = 0
        session['last_correct'] = None

    if session['q_index'] >= len(questions):
        if session['score'] >= target_score:
            return redirect(url_for('meta'))
        else:
            return redirect(url_for('result'))

    question = questions[session['q_index']]

    if request.method == 'POST':
        user_answer = request.form.get('answer', '').strip().lower()
        correct_answer = question['answer'].strip().lower()

        is_correct = user_answer == correct_answer
        session['last_correct'] = is_correct

        if is_correct:
            session['score'] += question['weight']

        session['q_index'] += 1
        return redirect(url_for('quiz'))

    return render_template(
        'quiz.html',
        question=question,
        score=session['score'],
        target=target_score,
        last_correct=session.get('last_correct')
    )


@app.route('/result')
def result():
    return render_template('result.html', score=session.get('score', 0))


@app.route('/meta')
def meta():
    return render_template('meta.html', score=session.get('score', 0))


if __name__ == '__main__':
    app.run(debug=True)
