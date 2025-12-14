from flask import Flask, request, jsonify
import pandas as pd
from flask_cors import CORS
from collections import defaultdict

app = Flask(__name__)
CORS(app)

def normalize_year(value):
    if value is None or pd.isna(value):
        return None
    value = str(value).strip().upper()
    mapping = {
        "I": "1", "II": "2", "III": "3", "IV": "4",
        "1": "1", "2": "2", "3": "3", "4": "4"
    }
    return mapping.get(value)

@app.route("/upload-excel", methods=["POST"])
def upload_excel():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    selected_year = normalize_year(request.form.get("year"))

    try:
        df = pd.read_excel(file, header=3)

        df = df.loc[:, ~df.columns.isna()]
        df.columns = [str(c) for c in df.columns]

        df["Branch"] = df["Branch"].ffill()
        df = df.dropna(subset=["YEAR", "Strength"])

        hall_columns = [
            c for c in df.columns
            if c.isdigit() and len(c) == 3
        ]

        hall_grouped = defaultdict(list)

        for _, row in df.iterrows():
            branch = str(row["Branch"])
            year = normalize_year(row["YEAR"])

            if selected_year and year != selected_year:
                continue

            for hall in hall_columns:
                val = row[hall]
                if pd.notna(val):
                    try:
                        count = int(float(val))
                        if count > 0:
                            hall_grouped[hall].append({
                                "department": branch,
                                "students_count": count,
                                "year": year
                            })
                    except:
                        pass

        for hall in hall_grouped:
            hall_grouped[hall].sort(
                key=lambda x: x["students_count"],
                reverse=True
            )

        print("✅ Detected halls:", hall_columns)
        print("✅ Data:", hall_grouped)

        return jsonify(hall_grouped)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
