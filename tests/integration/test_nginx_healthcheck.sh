#!/bin/sh

set -eu

project_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
suffix=$$
image="wasla-nginx-health-test:$suffix"
network="wasla-nginx-health-test-$suffix"
django_container="wasla-nginx-health-django-$suffix"
nginx_container="wasla-nginx-health-nginx-$suffix"

cleanup() {
    docker container stop "$nginx_container" "$django_container" >/dev/null 2>&1 || true
    docker container rm "$nginx_container" "$django_container" >/dev/null 2>&1 || true
    docker network rm "$network" >/dev/null 2>&1 || true
    docker image rm "$image" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

docker build --quiet --build-arg ENV=local --tag "$image" "$project_root" >/dev/null
docker network create "$network" >/dev/null

docker run --detach --name "$django_container" --network "$network" --network-alias django \
    --env ENV=production \
    --env DATABASE_TYPE=sqlite3 \
    --env SQLITE_NAME=/tmp/health.sqlite3 \
    --env SECRET_KEY=audit-only-secret-key-that-is-longer-than-fifty-characters-123456789 \
    --env ALLOWED_HOSTS=localhost,127.0.0.1 \
    --env TRUSTED_PROXY_COUNT=1 \
    --env AUTH_OTP_DELIVERY_BACKEND=apps.authentication.otp.WebhookOtpDeliveryBackend \
    --env AUTH_OTP_WEBHOOK_URL=https://sms.example.test/otp \
    --env AUTH_OTP_WEBHOOK_TOKEN=audit-token \
    "$image" \
    gunicorn project.asgi:application -k uvicorn_worker.UvicornWorker \
        --bind 0.0.0.0:8000 --workers 1 --timeout 30 >/dev/null

docker run --detach --name "$nginx_container" --network "$network" \
    --volume "$project_root/nginx/default.conf:/etc/nginx/conf.d/default.conf:ro" \
    nginx:1.30.4-alpine >/dev/null

attempt=0
until docker exec "$nginx_container" \
    wget --header "X-Forwarded-Proto: https" --quiet --tries=1 --spider \
        http://127.0.0.1/health/ 2>/dev/null
do
    attempt=$((attempt + 1))
    if [ "$attempt" -ge 20 ]; then
        docker logs "$django_container"
        docker logs "$nginx_container"
        exit 1
    fi
    sleep 1
done

PROJECT_ROOT="$project_root" NGINX_CONTAINER="$nginx_container" python3 - <<'PY'
import json
import os
import subprocess

project_root = os.environ["PROJECT_ROOT"]
nginx_container = os.environ["NGINX_CONTAINER"]
config = subprocess.run(
    [
        "docker",
        "compose",
        "--env-file",
        f"{project_root}/.env.example",
        "--file",
        f"{project_root}/docker-compose.yaml",
        "config",
        "--no-env-resolution",
        "--format",
        "json",
    ],
    check=True,
    capture_output=True,
    text=True,
)
healthcheck = json.loads(config.stdout)["services"]["nginx"]["healthcheck"]["test"]
if healthcheck[0] != "CMD":
    raise SystemExit(f"Expected an exec-form healthcheck, got: {healthcheck!r}")
subprocess.run(
    ["docker", "exec", nginx_container, *healthcheck[1:]],
    check=True,
)
PY
