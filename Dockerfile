FROM python:3.11

RUN apt update
RUN apt install libpq-dev python3-dev gcc -y
RUN python -m pip install pipenv

WORKDIR /app

ADD Pipfile Pipfile.lock /app/

RUN pipenv install --system --deploy --ignore-pipfile

COPY src/. /app
COPY entrypoint.sh /app

RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["sh", "./entrypoint.sh"]
