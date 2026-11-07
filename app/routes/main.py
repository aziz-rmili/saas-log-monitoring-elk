"""Routes de base : page d'accueil et vérification de l'état des services."""
from elasticsearch import Elasticsearch
from flask import Blueprint, jsonify, render_template
from pymongo import MongoClient
from redis import Redis

import config

main_bp = Blueprint("main", __name__)


def check_elasticsearch() -> dict:
    es = Elasticsearch(config.ES_HOST, request_timeout=3)
    health = es.cluster.health()
    return {"ok": health["status"] in ("green", "yellow"), "detail": health["status"]}


def check_mongodb() -> dict:
    client = MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=3000)
    client.admin.command("ping")
    return {"ok": True, "detail": "ping ok"}


def check_redis() -> dict:
    redis = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, socket_timeout=3)
    return {"ok": bool(redis.ping()), "detail": "ping ok"}


CHECKS = {
    "elasticsearch": check_elasticsearch,
    "mongodb": check_mongodb,
    "redis": check_redis,
}


def run_checks() -> dict:
    services = {}
    for name, check in CHECKS.items():
        try:
            services[name] = check()
        except Exception as exc:  # service injoignable
            services[name] = {"ok": False, "detail": type(exc).__name__}
    return services


@main_bp.route("/")
def index():
    return render_template("index.html", services=run_checks())


@main_bp.route("/health")
def health():
    services = run_checks()
    up = sum(1 for s in services.values() if s["ok"])
    if up == len(services):
        status = "healthy"
    elif up == 0:
        status = "down"
    else:
        status = "degraded"
    return jsonify(status=status, services=services), (200 if status != "down" else 503)
