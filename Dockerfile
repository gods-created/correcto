FROM python:3.12-alpine
COPY . /app
WORKDIR /app
EXPOSE 8001
RUN apk update
RUN chmod +x /app/entrypoint.sh
RUN python -m pip install --upgrade --no-cache-dir -r requirements.txt
ENTRYPOINT [ "/app/entrypoint.sh" ]
