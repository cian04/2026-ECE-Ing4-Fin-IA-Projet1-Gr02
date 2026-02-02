import pandas as pd
import torch
from pykeen.pipeline import pipeline
from pykeen.triples import TriplesFactory
from pathlib import Path

# =========================
# CHEMINS
# =========================
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "processed"
RELATIONS_PATH = DATA_DIR / "relations.csv"
OUTPUT_PATH = DATA_DIR / "predicted_links.csv"

# =========================
# 1. Charger les relations existantes
# =========================
relations = pd.read_csv(
    RELATIONS_PATH,
    usecols=["source_id", "relation_type", "target_id"]
)

relations.columns = ["head", "relation", "tail"]

# Conversion obligatoire pour PyKEEN
triples = relations[["head", "relation", "tail"]].values

# =========================
# 2. Créer la TriplesFactory
# =========================
tf = TriplesFactory.from_labeled_triples(triples)

# =========================
# 3. Entraîner le modèle (TransE)
# =========================
result = pipeline(
    training=tf,
    testing=tf,
    validation=tf,
    model="TransE",
    training_kwargs=dict(num_epochs=100),
    random_seed=42,
)

model = result.model

# =========================
# 4. Scorer les triplets existants
# =========================
mapped_triples = tf.mapped_triples

with torch.no_grad():
    scores = model.score_hrt(mapped_triples).squeeze()

# =========================
# 5. Sauvegarde CSV
# =========================
pred_df = pd.DataFrame({
    "head": relations["head"].values,
    "relation": relations["relation"].values,
    "tail": relations["tail"].values,
    "score": scores.cpu().numpy()
})

pred_df = pred_df.sort_values("score", ascending=False)

pred_df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")

print("✅ PRÉDICTION DE LIENS TERMINÉE")
print(f"→ {len(pred_df)} liens scorés")
print(f"→ Fichier généré : {OUTPUT_PATH}")
