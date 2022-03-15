# PoktBot

[![PyPI version](https://badge.fury.io/py/poktbot.svg)](https://badge.fury.io/py/poktbot)
[![Documentation Status](https://readthedocs.org/projects/poktbot/badge/?version=v0.0.1)](https://poktbot.readthedocs.io/en/v0.0.1/?badge=v0.0.1)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![stability-experimental](https://img.shields.io/badge/stability-experimental-orange.svg)](https://github.com/mkenney/software-guides/blob/master/STABILITY-BADGES.md#experimental)
![Docker Pulls](https://img.shields.io/docker/pulls/cryptonglab/poktbot)

PoktBot is a Telegram bot that was born with the mission of helping with the daily tracking of PocketNetwork nodes and their staking rewards.  

The bot is highly configurable, allowing to track many nodes at once, to generate graph/reports of rewards and to retrieve notifications based on detected errors and status, among other functionalities.

![graph](https://raw.githubusercontent.com/cryptonglab/poktbot/v0.0.1/docs/images/poktbot.gif "Graph")

## Docs
* [Getting started](https://poktbot.readthedocs.io/en/latest/).
* [Installation guide](https://poktbot.readthedocs.io/en/latest/installation/).
* [Configuration guide](https://poktbot.readthedocs.io/en/latest/configuration/).


## Features
* Provides an easy way to monitoring Pocket Network validator nodes status.
    * Errors monitoring and notification.  
    ![Cert-expiration](https://raw.githubusercontent.com/cryptonglab/poktbot/v0.0.1/docs/images/certificate_expiration_min.png "Certification expired")
    * Staking monitoring and notification.  
    ![Begin-unstake](https://raw.githubusercontent.com/cryptonglab/poktbot/v0.0.1/docs/images/begin_unstake_min.png "Begin unstake")
  

* Provides useful stats about node rewards and performance.  
    * Daily rewards.
    * Monthly rewards.
    * Graph of rewards evolution.  
    ![Stats-result](https://raw.githubusercontent.com/cryptonglab/poktbot/v0.0.1/docs/images/stats.png "Stats result")
  

* Multi-node and multi-user approach.
    * Average of stats with all configured nodes.
    * Robust RBAC system with two user levels:
        * Investor, only allowed viewing statistics of validators.
        * Admin, same than Investor but also able to add/remove admins, investors and nodes.
        
* Creation of economic reports to follow node economics or tax filing.  
![Balances](https://raw.githubusercontent.com/cryptonglab/poktbot/v0.0.1/docs/images/balances.png "Balances")
  
* Fully configurable behaviour. Every aspect of the bot is configurable with a configuration file, 
and some options through the bot interface itself.

## Current Status: Experimental
Code is new and may change or be removed in future versions. Please try it out and provide feedback. 
If it addresses a use-case that is important to you please open an issue to discuss it further.

Any opinion, bug found, improve request... will be welcome.

## Authors
* Iván de Paz (https://github.com/ipazc)
* Luis F monge (https://github.com/lucky-luk3)
