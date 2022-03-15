# Getting Started

{{project_name}} {{ version }} is a telegram-based bot designed to help tracking node rewards and error notifications. 
It uses *poktscan.com* for transactions/errors retrieval and *coingecko.com* as its prices backend. 

Once installed, the bot updates its internal database at a fixed rate with all the transactions and errors retrieved 
for a custom list of nodes. If a relevant event happens in any of the nodes, a telegram notification is raised. It 
can also be used to generate statistics, reports and for other management purposes. 

The bot contains a robust role-based access control system that makes it suitable for node pool owners where a group of
investors should be updated with their investment status. 


<img style="display: block; margin: auto;" src="images/poktbot.gif">
<p style="text-align: center; font-size: small; font-style: italic;">
Bot's admin interface. It can be added new nodes, new users and retrieve statistics on the fly.
</p>

Want to try it out? Follow [installation](installation.md) instructions and see it in action.