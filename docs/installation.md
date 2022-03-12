# Installation

Since {{project_name}} is a Telegram bot, it is first required to sign up a bot into Telegram by following these steps:

* Create a bot with [BotFather](https://core.telegram.org/bots#6-botfather) and write down the **BotId**.
* Login into [https://my.telegram.org](https://my.telegram.org) and create an **API-ID** and **APIHash**, then write them down too.
* Open a conversation with `@userinfobot`. This bot will send you your **TelegramId**, write it down. 

Those secrets are used by this package to use your created bot as the communication interface.

## Storage volume

{{project_name}} requires a storage to keep the database and the configuration files.

### 1. Create a storage volume for the bot

```bash
# Fill BOT_NAME with a unique name in this host for each bot to be run
# NOTE: don't use spaces and/or special characters
BOT_NAME="poktbot"

mkdir -p "${HOME}/.${BOT_NAME}/var/log/" && mkdir -p "${HOME}/.${BOT_NAME}/var/lib/" && mkdir -p "${HOME}/.${BOT_NAME}/config/"
```

### 2. Create the minimum config file

Here is a minimum configuration file, which requires to be tweaked to your data.

```bash
echo "---
    TELEGRAM_API:
        api_hash: <<YOUR API HASH>>
        api_id: <<YOUR API ID>>
        bot_token: <<YOUR BOT TOKEN>>

    IDS:
        admins_ids:
            - <<YOUR TELEGRAM ID>>
            - <<THE TELEGRAM ID OF THE ADMINISTRATOR 2>>
            ...
        investors_ids:
            - <<THE TELEGRAM ID OF THE INVESTOR 1>>
            - <<THE TELEGRAM ID OF THE INVESTOR 2>>
            ...

    SERVER:
        nodes:
            - <<YOUR NODE 1 ACCOUNT HASH>>
            - <<YOUR NODE 2 ACCOUNT HASH>>
            ...
" > "${HOME}/.${BOT_NAME}/config/config.yaml"
```

[https://poktbot.readthedocs.io/en/latest/configuration/](https://poktbot.readthedocs.io/en/latest/configuration/) for advanced configuration options.


## Installing from DOCKER

We have generated an official docker image {{project_name}} hosted at the docker hub that can be executed to handle 
the installation automatically. In case a manual installation is wanted, jump to section [section]. 

```bash
docker run -d \
    -v "$HOME/.${BOT_NAME}/config/":/etc/poktbot/ \
    -v "$HOME/.${BOT_NAME}/var/lib/":/var/lib/poktbot \
    -v "$HOME/.${BOT_NAME}/var/log/":/var/log/  \
    --restart always \
    --name ${BOT_NAME} \
    --hostname ${BOT_NAME} \
    poktbot:{{version}}
```

