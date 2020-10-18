##
# @author Xin Li <helloimlixin@gmail.com>
# @file Simple code snippet to send an email from an account to another.
# @desc Created on 2020-03-24 2:40:36 am
# @copyright Xin Li
#
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

MY_ADDRESS = "helloimlixin@outlook.com"
PASSWORD = "AndrewLee_94"


def send_mail(email, message, from_address, password):
    msg = MIMEMultipart()
    msg['From'] = from_address
    msg['To'] = email
    msg['Subject'] = "QRCode URL"
    msg.attach(MIMEText(message, 'plain'))
    sender = smtplib.SMTP(host='smtp-mail.outlook.com', port=587)
    sender.starttls()
    sender.login(from_address, password)
    sender.send_message(msg)
    del msg
    sender.quit()


if __name__ == '__main__':
    email = "bulixin@bu.edu"
    message = "https://qr.alipay.com/upxwfwna5v2xzuyka6"
    send_mail(email, message, MY_ADDRESS, PASSWORD)
