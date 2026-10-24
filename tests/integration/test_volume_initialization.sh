#!/bin/sh

set -eu

project_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
image="wasla-volume-init-test:$$"
media_volume="wasla-media-init-test-$$"
static_volume="wasla-static-init-test-$$"

cleanup() {
    docker volume rm -f "$media_volume" "$static_volume" >/dev/null 2>&1 || true
    docker image rm -f "$image" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

docker build --quiet --build-arg ENV=local --tag "$image" "$project_root" >/dev/null

assert_rejected_override() {
    variable=$1
    value=$2

    if docker run --rm --user 0:0 \
        --env "$variable=$value" \
        "$image" \
        /django/docker/initialize-volumes.sh >/dev/null 2>&1
    then
        echo "Volume initialization accepted unsafe $variable=$value." >&2
        exit 1
    fi
}

assert_rejected_override MEDIA_ROOT /tmp
assert_rejected_override STATIC_ROOT /tmp
assert_rejected_override DEFAULT_IMAGE_SOURCE /tmp/default.jpeg
assert_rejected_override APP_OWNER root:root

docker volume create "$media_volume" >/dev/null
docker volume create "$static_volume" >/dev/null

# Reproduce a volume created by root, which the unprivileged Django user cannot
# write to before initialization.
docker run --rm --user 0:0 \
    --volume "$media_volume:/django/media" \
    --volume "$static_volume:/django/staticfiles" \
    "$image" \
    sh -c 'mkdir -p /django/media/ads /django/staticfiles/admin && chmod -R 0700 /django/media /django/staticfiles'

docker run --rm --user 0:0 \
    --volume "$media_volume:/django/media" \
    --volume "$static_volume:/django/staticfiles" \
    "$image" \
    /django/docker/initialize-volumes.sh

docker run --rm --user django \
    --volume "$media_volume:/django/media" \
    --volume "$static_volume:/django/staticfiles" \
    "$image" \
    sh -c '
        test -r /django/media/default.jpeg
        test -w /django/media/ads
        test -w /django/staticfiles/admin
        touch /django/media/ads/upload-test.jpeg
        touch /django/staticfiles/admin/collectstatic-test.css
    '
