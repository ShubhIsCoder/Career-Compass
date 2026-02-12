FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml README.md /app/
COPY app /app/app
COPY run.py /app/run.py

RUN pip install --no-cache-dir -e .

ENV APP_ENV=production
EXPOSE 5000
CMD ["gunicorn", "-w", "2", "-k", "gthread", "-b", "0.0.0.0:5000", "run:app"]
