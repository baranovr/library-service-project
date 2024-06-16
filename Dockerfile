FROM python:3.12.2-alpine3.19
LABEL maintainer="rusipbox@gmail.com"

ENV PYTHOUNNBUFFERED 1

WORKDIR library/

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
