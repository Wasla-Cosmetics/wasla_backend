#!/bin/sh

set -eu

media_root=${MEDIA_ROOT:-/django/media}
static_root=${STATIC_ROOT:-/django/staticfiles}
default_image_source=${DEFAULT_IMAGE_SOURCE:-/django/default.jpeg}
app_owner=${APP_OWNER:-django:django}

if [ "$(id -u)" -ne 0 ]; then
    echo "Volume initialization must run as root." >&2
    exit 1
fi

if [ ! -f "$default_image_source" ]; then
    echo "Default image not found: $default_image_source" >&2
    exit 1
fi

mkdir -p "$media_root" "$static_root"

if [ ! -e "$media_root/default.jpeg" ]; then
    cp "$default_image_source" "$media_root/default.jpeg"
fi

chown -R "$app_owner" "$media_root" "$static_root"
chmod -R u+rwX "$media_root" "$static_root"
