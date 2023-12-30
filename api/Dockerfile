FROM python:latest
WORKDIR /app
COPY requirements.txt .

RUN pip install -r requirements.txt
# RUN alembic upgrade head

CMD python3 api.py