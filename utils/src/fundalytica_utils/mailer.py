# Documentation
# https://documentation.mailgun.com/en/latest/user_manual.html#sending-via-api

import yaml
import requests

from colorama import Fore

MAILGUN_URL = "https://api.mailgun.net/v3" # EU "https://api.eu.mailgun.net/v3"

def get_config(parameter):
    with open('/secret/mailgun.yml', 'r') as file:
        config = yaml.load(file, yaml.Loader)
        return config[parameter]

def send_simple_message(recipients, subject, text, sender=None, sender_name=None, admin=None):
    # use default sender
    if not sender:
        sender = get_config('default_sender_email')
        sender_name = get_config('default_sender_name')
    # add name to sender
    if sender_name:
        sender = f'{sender_name} <{sender}>'

    # add admin to recipients
    if admin:
        recipients.append(admin)

    recipients = utils.unique(recipients)

    url = f'{MAILGUN_URL}/{get_config("domain")}/messages'
    auth = ("api", get_config('api_key'))
    data = {"from": sender, "to": recipients, "subject": subject, "text": text}

    return requests.post(url, auth=auth, data=data)

if __name__ == "__main__":
    import utils

    recipients = [get_config('admin')]
    # recipients = ['test-4gmka8l4p@srv1.mail-tester.com']
    subject = 'Hello'
    text = 'This is Mailgun!'
    response = send_simple_message(recipients, subject, text)
    # response = send_simple_message(recipients, subject, text, admin=get_config('admin'))

    utils.cprint(recipients, Fore.CYAN)
    utils.cprint(f'{subject}: {text}', Fore.GREEN)
    utils.cprint(response, Fore.YELLOW)
    utils.cprint(response.text, Fore.MAGENTA)
else:
    from . import utils