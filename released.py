import os
import imaplib
import email
from email.header import decode_header
import re

EMAIL = 'your-email-must-is@outlook.com'
PASSWORD = 'your-outlook-password'
SERVER = 'imap-mail.outlook.com'

appdata_path = os.environ.get('APPDATA')
maomao_folder_path = os.path.join(appdata_path, 'Maomao')
if not os.path.exists(maomao_folder_path):
    os.makedirs(maomao_folder_path)
status_file_path = os.path.join(maomao_folder_path, 'email_status.txt')

def load_current_status():
    if os.path.exists(status_file_path):
        with open(status_file_path, 'r') as file:
            return file.read().strip()
    else:
        return 'a00'

def save_current_status(status):
    with open(status_file_path, 'w') as file:
        file.write(status)

def get_next_status(current_status):
    letter, number = current_status[0], int(current_status[1:])
    number += 1
    if number > 99:
        number = 1
        letter = chr(ord(letter) + 1)
    return f'{letter}{number:02d}'

def generate_next_email(base_email):
    current_status = load_current_status()
    next_status = get_next_status(current_status)
    save_current_status(next_status)
    parts = base_email.split('@')
    return f"{parts[0]}+{next_status}@{parts[1]}"

import requests
import time

def send_verification_request(email):
    url = "https://www.maomaovpn.com/api/v1/passport/comm/sendEmailVerify"
    payload = {"email": email}
    headers = {
        "Content-Type": "application/json",
        "Referrer-Policy": "strict-origin-when-cross-origin"
    }
    response = requests.post(url, json=payload, headers=headers)
    print(response)

base_email = "maomaocloud2024@outlook.com"
next_email = generate_next_email(base_email)
print("使用的email:", next_email)

send_verification_request(next_email)

print("wait 15...")
time.sleep(15)

mail = imaplib.IMAP4_SSL(SERVER)
mail.login(EMAIL, PASSWORD)
folders = ['Junk']

verification_code = None  

for folder in folders:
    mail.select('"{0}"'.format(folder))
    status, messages = mail.search(None, '(UNSEEN)')
    if status == 'OK':
        for mail_id in messages[0].split():
            status, data = mail.fetch(mail_id, '(RFC822)')
            for response_part in data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject = decode_header(msg["subject"])[0][0]
                    if isinstance(subject, bytes):
                        subject = subject.decode()
                    if subject == '猫猫云邮箱验证码':
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                if content_type in ["text/plain", "text/html"]:
                                    email_body = part.get_payload(decode=True).decode()
                                    match = re.search(r"\b\d{6}\b", email_body)
                                    if match:
                                        verification_code = match.group(0)  
                                        print('验证码:', verification_code)
                                        mail.store(mail_id, '+FLAGS', '\\Deleted')
                                        break  
                        else:
                            email_body = msg.get_payload(decode=True).decode()
                            match = re.search(r"\b\d{6}\b", email_body)
                            if match:
                                verification_code = match.group(0)  
                                print('验证码:', verification_code)
                                mail.store(mail_id, '+FLAGS', '\\Deleted')
                                break  
            mail.expunge()
            if verification_code:  
                break
    if verification_code:  
        break

mail.logout()

import requests

registration_data = {
    "email": next_email,
    "password": "Qwer...3",  
    "invite_code": "invite_code_here_if_u_need", 
    "email_code": verification_code
}

url = "https://www.maomaovpn.com/api/v1/passport/auth/register"

response = requests.post(url, data=registration_data)
print(response)
