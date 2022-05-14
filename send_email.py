#!/usr/bin/env python3

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv
import argparse
import os
import python_http_client
load_dotenv()


def main(message):
  emailmessage = Mail(
    from_email=os.environ.get('SENDGRID_EMAIL'),
    to_emails="chendeyao000@gmail.com",
    subject='Notification',
    html_content=message
  )

  sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
  response: python_http_client.client.Response = sg.send(emailmessage)
  return response

if __name__ == "__main__":
  parser = argparse.ArgumentParser("Send notification email")
  parser.add_argument("message", nargs="?", type=str, default="Alert (message not set)")
  args = parser.parse_args()
  response = main(args.message)
  print(response.status_code)
  print(response.body)
