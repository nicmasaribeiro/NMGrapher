FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt requirements-celery.txt ./
RUN pip install --no-cache-dir -r requirements-celery.txt
COPY . .
RUN useradd --create-home --uid 10001 grapher
USER grapher
ENV PYTHONUNBUFFERED=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
EXPOSE 5000
CMD ["python", "-m", "flask", "--app", "app", "run", "--host=0.0.0.0"]
