import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    PrecisionRecallDisplay,
    RocCurveDisplay,
    auc,
    confusion_matrix,
    precision_recall_curve,
    roc_curve,
)

# 1. Resolve paths relative to script location
SCRIPT_DIR = Path(__file__).resolve().parent
JSON_PATH = SCRIPT_DIR / "report.json"
CSV_PATH = SCRIPT_DIR / "GT1_201401.csv"

if not JSON_PATH.exists() and (SCRIPT_DIR / "reporte.json").exists():
    JSON_PATH = SCRIPT_DIR / "reporte.json"

# 2. Load JSON report
with open(JSON_PATH, "r", encoding="utf-8") as f:
    report_data = json.load(f)

report_scores = {}
for comp in report_data:
    for edge in comp.get("edges_trazability", []):
        pair = tuple(sorted(edge["pair"]))
        score = edge["details"].get("texte", 0.0)
        report_scores[pair] = score

# 3. Load Ground Truth CSV
preview = pd.read_csv(CSV_PATH, nrows=2, header=None)
delimiter = ";" if ";" in str(preview.iloc[0, 0]) else ","

df = pd.read_csv(CSV_PATH, sep=delimiter, header=None)

first_row_vals = [str(x).strip().upper() for x in df.iloc[0].values]
if any(val in ["OUI", "QUASI", "NO"] for val in first_row_vals):
    df.columns = ["node_1", "node_2", "label_raw"]
else:
    df = pd.read_csv(CSV_PATH, sep=delimiter)
    df.columns = ["node_1", "node_2", "label_raw"]

df["label_raw"] = df["label_raw"].astype(str).str.strip().str.upper()

# Binary classification target: OUI -> 1, QUASI -> 1, NO -> 0
label_map = {"OUI": 1, "QUASI": 1, "NO": 0}
df["y_true"] = df["label_raw"].map(label_map)

# 4. Lookup scores
def get_pair_score(row):
    pair = tuple(sorted([row["node_1"], row["node_2"]]))
    return report_scores.get(pair, 0.0)

df["score"] = df.apply(get_pair_score, axis=1)
df = df.sort_values(by="score", ascending=False).reset_index(drop=True)

# 5. Robust Business Thresholds (Ignoring 0.0 scores)
evaluated_df = df[df["score"] > 0.0]

# Conservative: Percentil 5 de las notas OUI verdaderas detectadas
oui_valid_scores = evaluated_df[evaluated_df["label_raw"] == "OUI"]["score"]
thresh_conservative = (
    np.percentile(oui_valid_scores, 5) if not oui_valid_scores.empty else 0.70
)

# Liberal: Máximo score entre las notas QUASI
quasi_valid_scores = evaluated_df[evaluated_df["label_raw"] == "QUASI"][
    "score"
]
thresh_liberal = (
    quasi_valid_scores.max() if not quasi_valid_scores.empty else 0.8991
)

# 6. Statistical Metrics (ROC, PR, Youden J, Max F1)
fpr, tpr, roc_thresholds = roc_curve(df["y_true"], df["score"])
roc_auc = auc(fpr, tpr)

precision, recall, pr_thresholds = precision_recall_curve(
    df["y_true"], df["score"]
)
f1_scores = 2 * (precision * recall) / (precision + recall + 1e-10)

# Filtrar umbrales <= 0.0 para calcular el F1 óptimo real
valid_pr_mask = pr_thresholds > 0.001
if np.any(valid_pr_mask):
    valid_f1 = f1_scores[:-1][valid_pr_mask]
    valid_thresh = pr_thresholds[valid_pr_mask]
    opt_f1_idx = np.argmax(valid_f1)
    thresh_f1 = valid_thresh[opt_f1_idx]
else:
    thresh_f1 = thresh_conservative

# Youden's J Index Threshold
valid_roc_mask = roc_thresholds > 0.001
if np.any(valid_roc_mask):
    youden_j = tpr[valid_roc_mask] - fpr[valid_roc_mask]
    opt_youden_idx = np.argmax(youden_j)
    thresh_youden = roc_thresholds[valid_roc_mask][opt_youden_idx]
else:
    thresh_youden = thresh_liberal

# 7. Output Results
print("=== THRESHOLD COMPARISON (ROBUST) ===")
print(
    f"1. Conservative Threshold (5th Pct OUI) : {thresh_conservative:.4f}"
)
print(f"2. Liberal Threshold (Highest QUASI)    : {thresh_liberal:.4f}")
print(f"3. Mathematical Optimal (Max F1 > 0)    : {thresh_f1:.4f}")
print(f"4. Mathematical Optimal (Youden J > 0)  : {thresh_youden:.4f}")
print("-" * 45)

# 8. Evaluate Confusion Matrices
thresholds_dict = {
    "Conservative (5th Pct)": thresh_conservative,
    "Liberal": thresh_liberal,
    "Optimal Max F1": thresh_f1,
    "Optimal Youden": thresh_youden,
}

for name, thresh in thresholds_dict.items():
    y_pred = (df["score"] >= thresh).astype(int)
    cm = confusion_matrix(df["y_true"], y_pred)
    tn, fp, fn, tp = cm.ravel()

    print(f"\nConfusion Matrix - {name} (Threshold = {thresh:.4f}):")
    print(f"  [ TN: {tn:4d} | FP: {fp:4d} ]")
    print(f"  [ FN: {fn:4d} | TP: {tp:4d} ]")

pd.set_option('display.max_rows', 200)
pd.set_option('display.min_rows', 200)
pd.set_option('display.width', 1000)

n = 100
print("\n=== TOP 100 PREDICTIONS ===")
print(df.head(n).to_string())

print("\n=== BOTTOM 100 PREDICTIONS ===")
print(df.tail(n).to_string())

# 9. Save Diagnostic Plot to File
fig, ax = plt.subplots(1, 2, figsize=(12, 5))

RocCurveDisplay(fpr=fpr, tpr=tpr, roc_auc=roc_auc).plot(ax=ax[0])
ax[0].set_title("ROC Curve")

PrecisionRecallDisplay(precision=precision, recall=recall).plot(ax=ax[1])
ax[1].set_title("Precision-Recall Curve")

plt.tight_layout()
output_plot_path = SCRIPT_DIR / "roc_pr_curves.png"
plt.savefig(output_plot_path, dpi=300)
plt.close(fig)

# 10. Save Evaluated CSV
output_csv_path = SCRIPT_DIR / "evaluation_results.csv"
df.to_csv(output_csv_path, index=False)