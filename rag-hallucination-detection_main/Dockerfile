FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY README.md README_REPRODUCE.md run_all_analysis.sh ./
COPY scripts/ ./scripts/
COPY human_eval_final/ ./human_eval_final/
COPY results/ ./results/

ENV PYTHONUNBUFFERED=1

CMD ["bash", "run_all_analysis.sh"]
