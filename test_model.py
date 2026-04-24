import joblib
import numpy as np
import pandas as pd
from datetime import datetime
import os

# Resolution robuste du modele: variable d'environnement puis fallback sur les noms connus.
MODEL_CANDIDATES = [
    os.getenv('PRICE_MODEL_PATH', '').strip(),
    'models/agricultural_prices_model_v1.pkl',
    'models/agricultural_prices_model_v1_fixed.pkl',
]


def resolve_model_path():
    for candidate in MODEL_CANDIDATES:
        if candidate and os.path.exists(candidate):
            return candidate
    return MODEL_CANDIDATES[1]


MODEL_PATH = resolve_model_path()

print("=" * 70)
print("🔍 TEST DU MODÈLE DANS VS CODE")
print("=" * 70)

try:
    # Chargement du package
    loaded_package = joblib.load(MODEL_PATH)
    loaded_model = loaded_package['model']
    feature_columns = loaded_package['feature_columns']  # Récupère l'ordre des features
    performance = loaded_package['performance']
    
    print("✅ CHARGEMENT RÉUSSI!")
    print(f"✅ Modèle: {loaded_package['model_name']}")
    print(f"✅ Version: {loaded_package['version']}")
    print(f"✅ Statut: {loaded_package['status']}")
    print(f"✅ Performance: RMSE = {performance['rmse']} USD, MAE = {performance['mae']} USD, R2 = {performance['r2']}")
    print(f"✅ Features attendues: {feature_columns}")
    print(f"✅ Config du modèle: {loaded_package['model_config']}")

    # Fonction de prédiction adaptée (basée sur votre predire_prix)
    def predire_prix(area_code, item_code, year, price_lag1, price_ma_3):
        """
        Fonction simple pour prédire un prix agricole avec des données d'exemple.
        """
        # Calcul des features cycliques (comme dans votre code)
        year_min, year_max = 1991, 2023
        normalized_year = (year - year_min) / (year_max - year_min)
        year_sin = np.sin(2 * np.pi * normalized_year)
        year_cos = np.cos(2 * np.pi * normalized_year)
        
        # Création des données d'entrée (adaptez les valeurs par défaut si besoin)
        input_data = pd.DataFrame([{
            'Price_lag1': price_lag1,
            'Price_MA_3': price_ma_3,
            'Year_sin': year_sin,
            'Year_cos': year_cos,
            'Year': year,
            'Crise_2008': 0,  # Par défaut pas de crise (changez à 1 si test d'une crise)
            'Area Code': area_code,
            'Item Code': item_code
        }])
        
        # Réorganisation selon l'ordre des features du modèle
        input_data = input_data[feature_columns]
        
        # Prédiction
        prix_pred = loaded_model.predict(input_data)[0]
        
        return round(prix_pred, 2)  # Arrondi pour lisibilité

    # Test de prédiction avec des valeurs d'exemple (adaptez-les à vos données réelles !)
    # Ex: area_code=1, item_code=100, year=2022, price_lag1=500, price_ma_3=550
    prediction = predire_prix(area_code=1, item_code=100, year=2022, price_lag1=500, price_ma_3=550)
    print("\n✅ TEST DE PRÉDICTION:")
    print(f"Prix prédit: {prediction} USD")
    
except Exception as e:
    print(f"❌ Échec du chargement ou test: {e}")
    print("Vérifiez : Le fichier est-il au bon endroit ? Les features correspondent-elles ?")

print("=" * 70)