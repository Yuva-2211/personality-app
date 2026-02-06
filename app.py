from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import torch
import torch.nn as nn
import numpy as np
from transformers import BertTokenizer, BertModel



app = FastAPI(title="Big Five Personality API")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

device = torch.device("cpu")



class BertMultiRegression(nn.Module):
    def __init__(self):
        super().__init__()
        self.bert = BertModel.from_pretrained("bert-base-uncased")
        self.dropout = nn.Dropout(0.1)
        self.regressor = nn.Linear(768, 5)

    def forward(self, input_ids, attention_mask):
        outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask
        )
        pooled = outputs.pooler_output
        pooled = self.dropout(pooled)
        return self.regressor(pooled)



tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
model = BertMultiRegression()
model.load_state_dict(
    torch.load("model/bert_final.pt", map_location="cpu")
)
model.eval()



def personality_rules(scores):
    A, O, C, E, N = scores

    def band(x):
        if x >= 0.65:
            return "High"
        elif x >= 0.35:
            return "Moderate"
        return "Low"

    labels = {
        "Agreeableness": band(A),
        "Openness": band(O),
        "Conscientiousness": band(C),
        "Extraversion": band(E),
        "Neuroticism": band(N),
    }

    profiles = []

    if N >= 0.65 and A >= 0.65:
        profiles.append("Emotionally sensitive with strong interpersonal concern")

    if N >= 0.65 and E < 0.35:
        profiles.append("Prone to anxiety with introverted tendencies")

    if N >= 0.65 and C < 0.35:
        profiles.append("Emotionally reactive with difficulty maintaining structure")

    if O >= 0.65 and C < 0.35:
        profiles.append("Highly creative but may struggle with organization")

    if O >= 0.65 and C >= 0.65:
        profiles.append("Intellectually curious with strong follow-through")

    if O < 0.35 and C >= 0.65:
        profiles.append("Conventional and highly disciplined")

    if C >= 0.65 and N < 0.35:
        profiles.append("Goal-oriented with emotional stability")

    if C >= 0.65 and E >= 0.65:
        profiles.append("Ambitious and socially engaged achiever")

    if E >= 0.65 and A >= 0.65:
        profiles.append("Warm and sociable with collaborative tendencies")

    if E >= 0.65 and A < 0.35:
        profiles.append("Assertive and socially dominant")

    if E < 0.35 and A >= 0.65:
        profiles.append("Reserved but cooperative and considerate")

    if N < 0.35 and E >= 0.65:
        profiles.append("Emotionally resilient and outgoing")

    if all(score >= 0.65 for score in scores):
        profiles.append("High across all dimensions (rare profile)")

    if all(score < 0.35 for score in scores):
        profiles.append("Low across all dimensions (rare profile)")

    if not profiles:
        profiles.append("Balanced personality with no extreme trait combinations")

    return labels, profiles


class TextInput(BaseModel):
    text: str


@app.post("/predict")
def predict(data: TextInput):

    inputs = tokenizer(
        data.text,
        return_tensors="pt",
        truncation=True,
        max_length=128
    )

    with torch.no_grad():
        outputs = model(
            inputs["input_ids"],
            inputs["attention_mask"]
        )

    preds = outputs.squeeze(0).cpu().numpy()

    trait_names = [
        "Agreeableness",
        "Openness",
        "Conscientiousness",
        "Extraversion",
        "Neuroticism"
    ]

    scores = {trait: float(score) for trait, score in zip(trait_names, preds)}

    _, profiles = personality_rules(preds)

    return {
        "scores": scores,
        "profiles": profiles
    }
