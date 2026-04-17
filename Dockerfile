FROM python:3.11-slim

WORKDIR /app

COPY python/requirements.txt /app/python/requirements.txt
RUN pip install --no-cache-dir -r /app/python/requirements.txt

COPY . /app

EXPOSE 8000

CMD ["uvicorn", "python.deploy_api:app", "--host", "0.0.0.0", "--port", "8000"]
