FROM python:3.12

ARG ENV=local
ARG UID=1000
ARG GID=1000

# set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# install system dependencies
RUN apt-get update \
    && apt-get -y install --no-install-recommends libpq-dev gcc curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /django

COPY requirements/ /django/requirements/

# Install dependencies
RUN pip install --upgrade pip \
    && case "${ENV}" in \
        dev) requirements_env=development ;; \
        stg|stage) requirements_env=staging ;; \
        prod) requirements_env=production ;; \
        *) requirements_env="${ENV}" ;; \
    esac \
    && pip install --no-cache-dir -r "requirements/${requirements_env}.txt"

# Copy project
COPY . /django/

RUN groupadd --gid "${GID}" django \
    && useradd --uid "${UID}" --gid "${GID}" --create-home django \
    && mkdir -p /django/media /django/staticfiles \
    && chown -R django:django /django

USER django
