FROM python:3.8
COPY . /app
WORKDIR /app

ENV TELEGRAM_API_session_path "/var/lib/poktbot/telegram/sessions/"
ENV SERVER_database_secret "/var/lib/poktbot/db/"
ENV SERVER_log_file_location "/var/log/poktbot.log"


RUN mkdir /etc/poktbot/ \
    && apt-get update \
    && apt-get install -y --no-install-recommends firefox-esr \
    && curl -L https://github.com/mozilla/geckodriver/releases/download/v0.30.0/geckodriver-v0.30.0-linux$(uname -m | awk -F'_' '{ print $2}').tar.gz | tar xz -C /usr/local/bin \
    && rm -fr /var/lib/apt/lists/*\
    && python setup.py install


CMD poktbot
