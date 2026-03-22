FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY restro_inventory ./restro_inventory
COPY main.py ./main.py
EXPOSE 8002
CMD ["uvicorn", "restro_inventory.main:app", "--host", "0.0.0.0", "--port", "8002"]
