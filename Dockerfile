FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY config ./config

RUN pip install --no-cache-dir .

# Two entrypoints, one image. The scheduler picks the subcommand:
#   docker run IMAGE predict --as-of now
#   docker run IMAGE score   --as-of now
ENTRYPOINT ["python", "-m", "openoutcry"]
CMD ["report"]
