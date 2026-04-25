from flask import Flask, render_template, request, redirect, url_for, jsonify
import joblib
import numpy as np
import pandas as pd
import os
import unicodedata
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
DEPLOY_MARKER = "api-v2-2026-04-25"
print(f"Deploy marker: {DEPLOY_MARKER}")

MODEL_CANDIDATES = [
    os.getenv("PRICE_MODEL_PATH", "").strip(),
    "models/agri_model_compact.pkl",
    "models/agricultural_prices_model_v1.pkl",
    "models/agricultural_prices_model_v1_fixed.pkl",
]


def resolve_model_path():
    for candidate in MODEL_CANDIDATES:
        if candidate and os.path.exists(candidate):
            return candidate
    return MODEL_CANDIDATES[1]


PRICE_MODEL_PATH = resolve_model_path()

try:
    price_package = joblib.load(PRICE_MODEL_PATH)
    PRICE_MODEL = price_package["model"]
    PRICE_FEATURE_COLUMNS = price_package.get("feature_columns", price_package.get("features", []))
    if not PRICE_FEATURE_COLUMNS:
        raise ValueError("Aucune liste de features trouvee dans le package modele.")
    print("Modele prix charge.")
except Exception as e:
    print(f"Erreur modele prix: {e}")
    PRICE_MODEL = None
    PRICE_FEATURE_COLUMNS = []

DEFAULT_COUNTRY_MAP = {
    "Tunisie": 222,
    "Algerie": 4,
    "Maroc": 145,
    "Libye": 124,
    "Egypte": 59,
    "Mauritanie": 136,
    "France": 68,
    "Italie": 106,
    "Espagne": 203,
    "Portugal": 174,
    "Grece": 82,
    "Turquie": 223,
    "Etats-Unis": 231,
    "Canada": 33,
    "Bresil": 21,
    "Argentine": 9,
    "Inde": 100,
    "Chine": 41,
    "Ukraine": 230,
    "Russie": 185,
    "Arabie Saoudite": 194,
    "Emirats Arabes Unis": 225,
    "Qatar": 179,
    "Koweit": 118,
    "Jordanie": 110,
    "Allemagne": 79,
    "Royaume-Uni": 229,
    "Pays-Bas": 157,
    "Belgique": 255,
    "Suisse": 211,
}

DEFAULT_ITEM_MAP = {
    # Cereales et bases alimentaires
    "Ble": 15,
    "Mais": 56,
    "Riz": 27,
    "Orge": 44,
    "Avoine": 75,

    # Legumineuses et oleagineux
    "Soja": 236,
    "Pois chiches": 191,
    "Feves": 176,
    "Lentilles": 201,
    "Tournesol": 267,

    # Cultures d'export
    "Cafe": 656,
    "Coton": 767,
    "Sucre": 156,

    # Produits cles du contexte tunisien
    "Olives": 260,
    "Dattes": 261,
    "Raisins": 567,
    "Amandes": 492,
    "Oranges": 490,
    "Pommes": 515,
    "Tomates": 388,
    "Pommes de terre": 116,
    "Oignons": 403,
    "Piments": 689,

    # Alias usuels (meme code)
    "Huile d olive (proxy Olives)": 260,
    "Dates": 261,
    "Grapes": 567,
    "Almonds": 492,
}


def normalize_text(value):
    text = str(value).strip()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return " ".join(text.split())


def resolve_data_path():
    candidates = [
        os.getenv("PRICE_DATA_PATH", "").strip(),
        "Prices_Data/Prices_E_All_Data.csv",
        "../Prices_Data/Prices_E_All_Data.csv",
        "../../Prices_Data/Prices_E_All_Data.csv",
    ]
    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate
    return ""


def order_countries(country_map):
    countries = sorted(country_map.keys())
    if "Tunisie" in countries:
        countries.remove("Tunisie")
        countries.insert(0, "Tunisie")
    return countries


def order_items(item_map):
    tunisian_priority = [
        "Olives",
        "Dattes",
        "Raisins",
        "Amandes",
        "Oranges",
        "Tomates",
        "Pommes de terre",
        "Oignons",
    ]
    items = sorted(item_map.keys())
    ordered = []
    for label in tunisian_priority:
        if label in items:
            ordered.append(label)
            items.remove(label)
    ordered.extend(items)
    return ordered


def load_dynamic_maps():
    data_path = resolve_data_path()
    if not data_path:
        print("CSV introuvable: utilisation des listes statiques.")
        return DEFAULT_COUNTRY_MAP.copy(), DEFAULT_ITEM_MAP.copy()

    try:
        cols = ["Area", "Area Code", "Item", "Item Code", "Element"]
        df = pd.read_csv(data_path, encoding="ISO-8859-1", usecols=lambda c: c in cols, low_memory=False)

        if "Element" in df.columns:
            df = df[df["Element"] == "Producer Price (USD/tonne)"]

        country_map = {}
        item_map = {}

        df_country = df[["Area", "Area Code"]].dropna().drop_duplicates()
        for _, row in df_country.iterrows():
            name = normalize_text(row["Area"])
            try:
                code = int(row["Area Code"])
            except Exception:
                continue
            country_map[name] = code

        df_item = df[["Item", "Item Code"]].dropna().drop_duplicates()
        for _, row in df_item.iterrows():
            name = normalize_text(row["Item"])
            try:
                code = int(row["Item Code"])
            except Exception:
                continue
            item_map[name] = code

        if not country_map or not item_map:
            raise ValueError("Maps vides apres lecture CSV")

        # Garder quelques alias utiles du contexte tunisien
        if "Dates" not in item_map and "Dattes" in item_map:
            item_map["Dates"] = item_map["Dattes"]
        if "Almonds" not in item_map and "Amandes" in item_map:
            item_map["Almonds"] = item_map["Amandes"]
        if "Grapes" not in item_map and "Raisins" in item_map:
            item_map["Grapes"] = item_map["Raisins"]

        print(f"Listes dynamiques chargees depuis {data_path}")
        print(f"Pays: {len(country_map)} | Produits: {len(item_map)}")
        return country_map, item_map
    except Exception as e:
        print(f"Erreur chargement CSV ({data_path}): {e}")
        print("Fallback vers listes statiques.")
        return DEFAULT_COUNTRY_MAP.copy(), DEFAULT_ITEM_MAP.copy()


COUNTRY_MAP, ITEM_MAP = load_dynamic_maps()
COUNTRY_OPTIONS = order_countries(COUNTRY_MAP)
ITEM_OPTIONS = order_items(ITEM_MAP)


def predire_prix(area_code, item_code, year, price_lag1, price_ma_3, crise_2008=0):
    year_min, year_max = 1991, 2023
    normalized_year = (year - year_min) / (year_max - year_min)
    year_sin = np.sin(2 * np.pi * normalized_year)
    year_cos = np.cos(2 * np.pi * normalized_year)

    input_data = pd.DataFrame(
        [
            {
                "Price_lag1": price_lag1,
                "Price_MA_3": price_ma_3,
                "Year_sin": year_sin,
                "Year_cos": year_cos,
                "Year": year,
                "Crise_2008": crise_2008,
                "Area Code": area_code,
                "Item Code": item_code,
            }
        ]
    )

    input_data = input_data[PRICE_FEATURE_COLUMNS]
    return PRICE_MODEL.predict(input_data)[0]


def run_forecast(area_name, item_name, base_year, num_future, price_minus2, price_minus1, base_price):
    if PRICE_MODEL is None:
        raise ValueError("Modele de prix non charge.")

    area_code = COUNTRY_MAP.get(area_name)
    if area_code is None:
        raise ValueError("Pays non reconnu.")

    item_code = ITEM_MAP.get(item_name)
    if item_code is None:
        raise ValueError("Produit non reconnu.")

    if num_future < 1:
        raise ValueError("Nombre d'annees futures doit etre au moins 1.")

    recent_prices = [price_minus2, price_minus1, base_price]
    predictions = []
    current_year = base_year + 1

    for _ in range(num_future):
        lag1 = recent_prices[-1]
        ma3 = sum(recent_prices[-3:]) / 3
        pred = predire_prix(area_code, item_code, current_year, lag1, ma3)
        pred_rounded = round(pred, 1)
        predictions.append((current_year, pred_rounded))
        recent_prices.append(pred_rounded)
        current_year += 1

    all_prices = [base_price] + [p[1] for p in predictions]
    variations = []
    for i in range(1, len(all_prices)):
        var = (all_prices[i] - all_prices[i - 1]) / all_prices[i - 1] * 100
        variations.append(round(var, 1))

    variation_totale = (all_prices[-1] - base_price) / base_price * 100 if len(all_prices) > 1 else 0
    variation_totale = round(variation_totale, 1)

    tendances = []
    for var in variations:
        if var > 0:
            tendances.append("Hausse")
        elif var < 0:
            tendances.append("Baisse")
        else:
            tendances.append("Stabilisation")

    if variation_totale > 0:
        tendance_globale = "Hausse"
    elif variation_totale < 0:
        tendance_globale = "Baisse"
    else:
        tendance_globale = "Stable"

    return {
        "item": item_name,
        "country": area_name,
        "base_year": base_year,
        "base_price": round(base_price, 1),
        "predictions": predictions,
        "variations": variations,
        "variation_totale": variation_totale,
        "tendances": tendances,
        "tendance_globale": tendance_globale,
    }


@app.route("/")
def index():
    return redirect(url_for("price_prediction"))


@app.route("/price_prediction", methods=["GET", "POST"])
def price_prediction():
    results = None
    form_data = {}

    if request.method == "POST":
        form_data = request.form.to_dict()
        try:
            area_name = request.form["area_name"]
            item_name = request.form["item_name"]
            base_year = int(request.form["base_year"])
            num_future = int(request.form["num_future"])
            price_minus2 = float(request.form["price_minus2"])
            price_minus1 = float(request.form["price_minus1"])
            base_price = float(request.form["base_price"])

            results = run_forecast(
                area_name=area_name,
                item_name=item_name,
                base_year=base_year,
                num_future=num_future,
                price_minus2=price_minus2,
                price_minus1=price_minus1,
                base_price=base_price,
            )
        except Exception as e:
            results = {"error": str(e)}

    return render_template(
        "price_prediction.html",
        results=results,
        form_data=form_data,
        countries=COUNTRY_OPTIONS,
        items=ITEM_OPTIONS,
    )


@app.route("/api/meta", methods=["GET"])
def api_meta():
    return jsonify({
        "countries": COUNTRY_OPTIONS,
        "items": ITEM_OPTIONS,
        "model_loaded": PRICE_MODEL is not None,
    })


@app.route("/api/predict/price", methods=["POST"])
def api_predict_price():
    payload = request.get_json(silent=True) or {}
    try:
        area_name = str(payload.get("area_name", "")).strip()
        item_name = str(payload.get("item_name", "")).strip()
        base_year = int(payload.get("base_year"))
        num_future = int(payload.get("num_future"))
        price_minus2 = float(payload.get("price_minus2"))
        price_minus1 = float(payload.get("price_minus1"))
        base_price = float(payload.get("base_price"))

        if not area_name or not item_name:
            raise ValueError("area_name et item_name sont obligatoires.")

        result = run_forecast(
            area_name=area_name,
            item_name=item_name,
            base_year=base_year,
            num_future=num_future,
            price_minus2=price_minus2,
            price_minus1=price_minus1,
            base_price=base_price,
        )

        api_predictions = [{"year": y, "price": p} for y, p in result["predictions"]]
        api_result = {
            **result,
            "predictions": api_predictions,
            "tendance_globale": result["tendance_globale"].lower(),
        }
        return jsonify(api_result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(debug=False, host="0.0.0.0", port=port)