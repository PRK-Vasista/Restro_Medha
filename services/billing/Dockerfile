FROM python:3.12-slim
WORKDIR /app
# Shared observability (build context = repository root)
COPY libs/observability /tmp/observability
RUN pip install --no-cache-dir /tmp/observability
COPY services/billing/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/billing/restro_billing ./restro_billing
COPY services/billing/main.py ./main.py
EXPOSE 8001
CMD ["uvicorn", "restro_billing.main:app", "--host", "0.0.0.0", "--port", "8001"]
