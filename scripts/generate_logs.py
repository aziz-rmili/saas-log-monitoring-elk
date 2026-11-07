#!/usr/bin/env python3
"""Génère des logs SaaS de test (CSV + JSON Lines) avec Faker.

Exemples :
    python scripts/generate_logs.py                 # 10 000 logs dans data/
    python scripts/generate_logs.py -n 500 --seed 1 # 500 logs reproductibles
"""
import argparse
import csv
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

from faker import Faker

SERVICES = ["auth-service", "billing", "api-gateway", "notification", "search"]
ENDPOINTS = ["/api/v1/users", "/api/v1/login", "/api/v1/orders", "/api/v1/invoices",
             "/api/v1/search", "/api/v1/reports", "/api/v1/settings"]
FIELDS = ["@timestamp", "level", "service", "endpoint", "http_status",
          "response_time_ms", "user_id", "client_ip", "message"]

MESSAGES = {
    "DEBUG": ["Cache lookup", "Query plan computed", "Request headers parsed"],
    "INFO": ["Request completed", "User authenticated", "Invoice generated", "Search executed"],
    "WARNING": ["Slow query detected", "Invalid input received", "Retrying upstream call", "Rate limit almost reached"],
    "ERROR": ["Database connection timeout", "Upstream service unavailable", "Unhandled exception in handler"],
    "CRITICAL": ["Database connection pool exhausted", "Service crashed, restarting"],
}


def pick_status_and_level():
    """Choisit un statut HTTP puis un niveau cohérent avec ce statut."""
    r = random.random()
    if r < 0.82:
        return random.choice([200, 200, 200, 201, 204]), random.choices(["INFO", "DEBUG"], [8, 2])[0]
    if r < 0.93:
        return random.choice([400, 401, 403, 404, 429]), "WARNING"
    if r < 0.99:
        return random.choice([500, 500, 502, 503]), "ERROR"
    return 500, "CRITICAL"


def make_log(fake: Faker, now: datetime, days: int) -> dict:
    status, level = pick_status_and_level()
    # temps de réponse : la plupart rapides, quelques-uns lents (> 3 s) utiles pour l'alerting
    response = random.lognormvariate(5.3, 0.6)
    if status >= 500 or random.random() < 0.02:
        response += random.uniform(1500, 4500)
    ts = now - timedelta(seconds=random.randint(0, days * 86400))
    return {
        "@timestamp": ts.strftime("%Y-%m-%dT%H:%M:%S.") + f"{random.randint(0, 999):03d}Z",
        "level": level,
        "service": random.choice(SERVICES),
        "endpoint": random.choice(ENDPOINTS),
        "http_status": status,
        "response_time_ms": round(response, 1),
        "user_id": f"user_{random.randint(1, 300)}",
        "client_ip": fake.ipv4_public(),
        "message": random.choice(MESSAGES[level]),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-n", "--count", type=int, default=10000, help="nombre de logs (défaut : 10000)")
    parser.add_argument("--days", type=int, default=7, help="période couverte en jours (défaut : 7)")
    parser.add_argument("--seed", type=int, default=42, help="graine aléatoire (défaut : 42)")
    parser.add_argument("--out", default="data", help="dossier de sortie (défaut : data)")
    args = parser.parse_args()

    random.seed(args.seed)
    Faker.seed(args.seed)
    fake = Faker("fr_FR")
    now = datetime.now(timezone.utc)

    logs = sorted((make_log(fake, now, args.days) for _ in range(args.count)), key=lambda d: d["@timestamp"])

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "logs_test.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(logs)
    with open(out / "logs_test.json", "w", encoding="utf-8") as f:
        for log in logs:
            f.write(json.dumps(log, ensure_ascii=False) + "\n")

    print(f"{len(logs)} logs générés : {out / 'logs_test.csv'} et {out / 'logs_test.json'}")


if __name__ == "__main__":
    main()
