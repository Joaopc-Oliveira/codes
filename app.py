from flask import Flask, request, render_template
import numpy as np
import joblib
import pyodbc

app = Flask(__name__)
model = joblib.load('random_forest_model3.pkl')

# Configurações do banco de dados
server = 'kicc-prediction.database.windows.net'
database = 'predictions'
username = 'jpoliveira'
password = 'r7M!2#n4'
driver = '{ODBC Driver 17 for SQL Server}'

@app.route('/')
def home():
    return render_template('form.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Conecta ao banco de dados
        conn = pyodbc.connect(
            f'DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password}'
        )
        cursor = conn.cursor()

        # Coleta dados do formulário
        age = int(request.form['Age'])
        resting_bp = int(request.form['RestingBP'])
        cholesterol = int(request.form['Cholesterol'])
        fasting_bs = int(request.form['FastingBS'])
        max_hr = int(request.form['MaxHR'])
        oldpeak = float(request.form['Oldpeak'])
        sex_m = int(request.form['Sex_M'])

        chest_pain = request.form['ChestPainType']
        ecg = request.form['RestingECG']
        exercise_angina = request.form['ExerciseAngina']
        slope = request.form['ST_Slope']

        # One-hot encoding
        chest_pain_ata = 1 if chest_pain == 'ATA' else 0
        chest_pain_nap = 1 if chest_pain == 'NAP' else 0
        chest_pain_ta = 1 if chest_pain == 'TA' else 0

        ecg_normal = 1 if ecg == 'Normal' else 0
        ecg_st = 1 if ecg == 'ST' else 0

        angina_y = 1 if exercise_angina == 'Y' else 0

        slope_flat = 1 if slope == 'Flat' else 0
        slope_up = 1 if slope == 'Up' else 0

        # Vetor de características
        features = np.array([[age, resting_bp, cholesterol, fasting_bs, max_hr, oldpeak,
                              sex_m, chest_pain_ata, chest_pain_nap, chest_pain_ta,
                              ecg_normal, ecg_st, angina_y, slope_flat, slope_up]])

        prediction = model.predict(features)[0]
        result = 'High Risk of Heart Disease' if prediction == 1 else 'Low Risk of Heart Disease'

        # Armazena a previsão no banco de dados
        cursor.execute("""
            INSERT INTO predictions_log
            (age, resting_bp, cholesterol, fasting_bs, max_hr, oldpeak,
             sex_m, chest_pain_type, ecg_type, exercise_angina, st_slope, result)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (age, resting_bp, cholesterol, fasting_bs, max_hr, oldpeak,
              sex_m, chest_pain, ecg, exercise_angina, slope, result))
        conn.commit()

        return f"<h2>{result}</h2><br><a href='/'>Try again</a>"

    except Exception as e:
        return f"<h3>Error: {e}</h3><br><a href='/'>Back</a>"

if __name__ == '__main__':
    app.run()
