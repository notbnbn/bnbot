FROM python:3

COPY main.py /
COPY /bnbot /bnbot

ENV PYTHONUNBUFFERED=1

RUN pip install discord.py \
    pyaml \
    psycopg2

CMD ["python", "main.py"]