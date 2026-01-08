FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install gunicorn

COPY . /app/

EXPOSE 8000


# CMD python manage.py migrate && \
#     python manage.py collectstatic --noinput && \
#     gunicorn WebScanner.wsgi:application --bind 0.0.0.0:8000

CMD ["sh", "-c", "python manage.py migrate && python manage.py seed_markers && python manage.py collectstatic --noinput && gunicorn WebScanner.wsgi:application --bind 0.0.0.0:8000"]
