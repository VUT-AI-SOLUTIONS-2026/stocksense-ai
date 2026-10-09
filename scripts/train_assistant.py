"""Train on example questions, select confidence on validation, then score held-out questions."""
import json
from pathlib import Path

import joblib

from stocksense.assistant import normalise, train_intents

ROOT = Path(__file__).resolve().parents[1]


def score(model, rows):
    results = [{**row, "predicted": model.classify(row["text"])} for row in rows]
    return {"correct": sum(row["intent"] == row["predicted"] for row in results),
            "total": len(results), "questions": results}


def main():
    corpus = json.loads((ROOT / "resources/assistant_questions.json").read_text(encoding="utf-8"))
    seen = set()
    for split in ("train", "validation", "development_check", "development_unsupported", "test", "unsupported_test"):
        for row in corpus[split]:
            cleaned = normalise(row["text"])
            if cleaned in seen:
                raise ValueError("Repeated question after normalisation; review the split.")
            seen.add(cleaned)
    model = train_intents(corpus["train"])
    candidates = []
    for threshold in (0.35, 0.45, 0.55):
        model.threshold = threshold
        report = score(model, corpus["validation"])
        candidates.append({"threshold": threshold, "correct": report["correct"], "total": report["total"]})
    # Prefer stronger rejection when validation scores tie. Test labels play no part.
    chosen = max(candidates, key=lambda row: (row["correct"], row["threshold"]))
    model.threshold = chosen["threshold"]
    report = {"training_questions": len(corpus["train"]), "threshold": model.threshold,
              "validation_candidates": candidates, "held_out": score(model, corpus["test"]),
              "unsupported": score(model, corpus["unsupported_test"]),
              "development_check": score(model, corpus["development_check"]),
              "initial_check": "The original 25/8 question sets scored 16/25 and 7/8 before stop-word removal. They are now development data, not fresh held-out evidence.",
              "limitations": "Small curated English question set; independent group and user testing still needed."}
    output = ROOT / "artifacts/assistant"
    output.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output / "intent_model.joblib")
    (output / "evaluation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Confidence threshold: {model.threshold}")
    for name in ("held_out", "unsupported"):
        print(f"{name}: {report[name]['correct']}/{report[name]['total']}")


if __name__ == "__main__":
    main()
