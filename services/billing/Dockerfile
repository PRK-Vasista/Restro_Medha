FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY restro_billing ./restro_billing
COPY main.py ./main.py
EXPOSE 8001
CMD ["uvicorn", "restro_billing.main:app", "--host", "0.0.0.0", "--port", "8001"]
