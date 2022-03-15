# Installation

## First steps
Since **{{project_name}}** is a Telegram bot, the first step is to sign up a bot into Telegram by following these steps:

* Create a bot with [BotFather](https://core.telegram.org/bots#6-botfather) and write down the **BotId**.
* Modify you bot in [BotFather](https://core.telegram.org/bots#6-botfather) in `/mybots` menu. Select your bot and `Edit bot`, after that modify commands in `Edit Commands`. Write `menu - Main Menu` and send the message.
* Login into [https://my.telegram.org](https://my.telegram.org) and create an **API-ID** and **APIHash**, then write them down too.
* Open a conversation with `@userinfobot`. This bot will send you your **TelegramId**, write it down. 

Those secrets are used by this package to use your created bot as the communication interface.

## Storage volume

**{{project_name}}** requires a storage to keep the database and the configuration files.

### 1. Create a storage volume for the bot

```bash
# Fill BOT_NAME with a unique name in this host for each bot to be run
# NOTE: don't use spaces and/or special characters
BOT_NAME="{{project_name_lowercase}}"

mkdir -p "${HOME}/.${BOT_NAME}/var/log/" && mkdir -p "${HOME}/.${BOT_NAME}/var/lib/" && mkdir -p "${HOME}/.${BOT_NAME}/config/"
```

### 2. Create the minimum config file

Here is a minimum configuration file that requires to be tweaked to your data.

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

[https://{{project_name_lowercase}}.readthedocs.io/en/v{{version}}/configuration/](https://{{project_name_lowercase}}.readthedocs.io/en/v{{version}}/configuration/) for advanced configuration options.


## Installation with DOCKER

We have generated an official docker image **{{project_name}}** hosted at the docker hub that can be executed to handle 
the installation automatically. In case a manual installation is wanted, jump to section [Building the image]. 

```bash
docker run -d \
    -v "${HOME}/.${BOT_NAME}/config/":/etc/{{project_name_lowercase}}/ \
    -v "${HOME}/.${BOT_NAME}/var/lib/":/var/lib/{{project_name_lowercase}} \
    -v "${HOME}/.${BOT_NAME}/var/log/":/var/log/  \
    --restart always \
    --name ${BOT_NAME} \
    --hostname ${BOT_NAME} \
    cryptonglab/{{project_name_lowercase}}:{{version}}
```

### Building the image

In some restricted environments, you would want to build the image manually. 
It can be done by cloning this repository and building it with `docker build`:

```bash
git clone https://github.com/cryptonglab/{{project_name_lowercase}}.git -b "v{{version}}"
cd {{project_name_lowercase}}
docker build . -t cryptonglab/{{project_name_lowercase}}:{{version}}
```

After the building process finishes, the same docker run command can be executed, which will use the local image you
have just built instead of downloading it from the docker hub repository:

```bash
docker run -d \
    -v "${HOME}/.${BOT_NAME}/config/":/etc/{{project_name_lowercase}}/ \
    -v "${HOME}/.${BOT_NAME}/var/lib/":/var/lib/{{project_name_lowercase}} \
    -v "${HOME}/.${BOT_NAME}/var/log/":/var/log/  \
    --restart always \
    --name ${BOT_NAME} \
    --hostname ${BOT_NAME} \
    cryptonglab/{{project_name_lowercase}}:{{version}}
```

[Building the image]: #building-the-image

## Installation with PIP

Even though we encourage the installation with docker, **{{project_name}}** can also be installed with pip since it is 
also part of the [Python Package Index repository](https://pypi.org/project/{{project_name_lowercase}}/).

```bash
pip install {{project_name_lowercase}}=={{version}}
```

Once installed, a CMD tool with the name `{{project_name_lowercase}}` will be available to run the bot, but certain environment variables
related to the storage volume should be set before running it:

```bash
TELEGRAM_API_session_path="${HOME}/.${BOT_NAME}/var/lib/telegram/sessions/" \
    SERVER_database_secret="${HOME}/.${BOT_NAME}/var/lib/db/" \
    SERVER_log_file_location="${HOME}/.${BOT_NAME}/var/log/{{project_name_lowercase}}.log" \
    CONFIG_PATH="${HOME}/.${BOT_NAME}/config/config.yaml" \
    {{project_name_lowercase}}
```

### Installation with PIP from repository

In restricted environments, installing from the repository is also possible. The release version {{version}} is tagged 
within the repository so that it can be installed with PIP:

```bash
pip install git+https://github.com/cryptonglab/{{project_name_lowercase}}@v{{version}}
```

Once installed, a CMD tool with the name `{{project_name_lowercase}}` will be available to run the bot, but certain environment variables
related to the storage volume should be set before running it:

```bash
TELEGRAM_API_session_path="${HOME}/.${BOT_NAME}/var/lib/telegram/sessions/" \
    SERVER_database_secret="${HOME}/.${BOT_NAME}/var/lib/db/" \
    SERVER_log_file_location="${HOME}/.${BOT_NAME}/var/log/{{project_name_lowercase}}.log" \
    CONFIG_PATH="${HOME}/.${BOT_NAME}/config/config.yaml" \
    {{project_name_lowercase}}
```

### Installation with python from repository

If the source code is downloaded, for example:

```bash
git clone https://github.com/cryptonglab/{{project_name_lowercase}}.git -b "v{{version}}"
```

It can be installed with python as follows:
```bash
cd {{project_name_lowercase}}
python setup.py install
```

Once installed, a CMD tool with the name `{{project_name_lowercase}}` will be available to run the bot, but certain environment variables
related to the storage volume should be set before running it:

```bash
TELEGRAM_API_session_path="${HOME}/.${BOT_NAME}/var/lib/telegram/sessions/" \
    SERVER_database_secret="${HOME}/.${BOT_NAME}/var/lib/db/" \
    SERVER_log_file_location="${HOME}/.${BOT_NAME}/var/log/{{project_name_lowercase}}.log" \
    CONFIG_PATH="${HOME}/.${BOT_NAME}/config/config.yaml" \
    {{project_name_lowercase}}
```
