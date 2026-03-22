FROM python:3.12-slim
WORKDIR /app
COPY libs/observability /tmp/observability
RUN pip install --no-cache-dir /tmp/observability
COPY services/inventory/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/inventory/restro_inventory ./restro_inventory
COPY services/inventory/main.py ./main.py
EXPOSE 8002
CMD ["uvicorn", "restro_inventory.main:app", "--host", "0.0.0.0", "--port", "8002"]
