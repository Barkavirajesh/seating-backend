from flask import Flask, request, jsonify
import pandas as pd
from flask_cors import CORS
from collections import defaultdict

app = Flask(__name__)
CORS(app)

def normalize_year(value):
    """Convert Roman numerals or floats to integer year as string."""
    if value is None:
        return None
    value = str(value).strip().upper()
    roman_map = {"I": "1", "II": "2", "III": "3", "IV": "4"}
    if value in roman_map:
        return roman_map[value]
    try:
        return str(int(float(value)))
    except:
        return None

@app.route('/upload-excel', methods=['POST'])
def upload_excel():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']

    # ✅ Normalize selected year coming from React
    selected_year = normalize_year(request.form.get("year"))

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        df = pd.read_excel(file, header=4)
        df = df.iloc[:, 1:]
        df['Branch'] = df['Branch'].ffill()
        df = df.dropna(subset=['YEAR', 'Strength'])

        hall_grouped = defaultdict(list)

        for _, row in df.iterrows():
            branch = str(row['Branch']).strip()
            year = normalize_year(row['YEAR'])

            # ✅ Correct year filtering
            if selected_year and year != selected_year:
                continue

            for col in df.columns:
                if col not in ['S.No.', 'Branch', 'YEAR', 'Strength', 'Boys', 'Girls', 'TOTAL']:
                    try:
                        val_int = int(float(row[col]))
                        if val_int > 0:
                            hall_grouped[col.strip()].append({
                                "students_count": val_int,
                                "department": branch,
                                "year": year
                            })
                    except (ValueError, TypeError):
                        continue

        for hall in hall_grouped:
            hall_grouped[hall] = sorted(
                hall_grouped[hall],
                key=lambda x: x["students_count"],
                reverse=True
            )

        return jsonify(hall_grouped)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)