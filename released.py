import os
import imaplib
import email
from email.header import decode_header
import re
import requests
import json
import time

EMAIL = 'your_email_must_is@outlook.com' #email here
PASSWORD = 'your_outlook_passw' #passw here
SERVER = 'imap-mail.outlook.com'

# 设置保存文件的路径
appdata_path = os.environ.get('APPDATA')
maomao_folder_path = os.path.join(appdata_path, 'Maomao')
if not os.path.exists(maomao_folder_path):
    os.makedirs(maomao_folder_path)
status_file_path = os.path.join(maomao_folder_path, 'email_status.txt')
subscribe_file_path = os.path.join(maomao_folder_path, 'subscribe_url.txt')  # 订阅URL文件的路径

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

def send_verification_request(email):
    url = "https://www.maomaovpn.com/api/v1/passport/comm/sendEmailVerify"
    payload = {"email": email}
    headers = {
        "Content-Type": "application/json",
        "Referrer-Policy": "strict-origin-when-cross-origin"
    }
    response = requests.post(url, json=payload, headers=headers)
    print(response)

iteration_count = int(input("Enter the number of iterations: "))

for _ in range(iteration_count):
    base_email = "your@outlook.com" #email here
    next_email = generate_next_email(base_email)
    print("使用的email:", next_email)

    send_verification_request(next_email)

    print("wait 10...")
    time.sleep(10)

    mail = imaplib.IMAP4_SSL(SERVER)
    mail.login(EMAIL, PASSWORD)
    folders = ['inbox', 'Junk']

    emails_info = {}

    for folder in folders:
        mail.select('"{0}"'.format(folder))
        status, messages = mail.search(None, '(UNSEEN)')
        if status == 'OK':
            emails_info[folder] = []
            for mail_id in messages[0].split():
                status, data = mail.fetch(mail_id, '(RFC822)')
                for response_part in data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        subject = decode_header(msg["subject"])[0][0]
                        if isinstance(subject, bytes):
                            subject = subject.decode()
                        if subject == '猫猫云邮箱验证码':
                            email_info = {'Subject': subject}
                            if msg.is_multipart():
                                for part in msg.walk():
                                    content_type = part.get_content_type()
                                    if content_type in ["text/plain", "text/html"]:
                                        email_body = part.get_payload(decode=True).decode()
                                        match = re.search(r"\b\d{6}\b", email_body)
                                        if match:
                                            email_info['验证码'] = match.group(0)
                            else:
                                email_body = msg.get_payload(decode=True).decode()
                                match = re.search(r"\b\d{6}\b", email_body)
                                if match:
                                    email_info['验证码'] = match.group(0)
                            if '验证码' in email_info:
                                emails_info[folder].append(email_info)

    verification_codes = []
    for folder, emails in emails_info.items():
        for email_info in emails:
            if '验证码' in email_info:
                verification_code = str(email_info['验证码'])
                verification_codes.append(verification_code)
                print(verification_code)

    for folder in folders:
        mail.select('"{0}"'.format(folder), readonly=False)
        status, messages = mail.search(None, 'ALL')
        if status == 'OK':
            for mail_id in messages[0].split():
                mail.store(mail_id, '+FLAGS', '\\Deleted')
            mail.expunge()

    mail.logout()

    if verification_codes:
        verification_code = verification_codes[-1]

        registration_data = {
            "email": next_email,
            "password": "Qwer...3",
            "invite_code": "YSirkEU4",
            "email_code": verification_code
        }

        url = "https://www.maomaovpn.com/api/v1/passport/auth/register"
        response = requests.post(url, data=registration_data)
        print(response)
        if response.status_code == 500:
            print("Error during registration, exiting...")
            break

        time.sleep(5)

        url = "https://www.maomaovpn.com/api/v1/passport/auth/login"
        login_payload = {
            "email": next_email,
            "password": "Qwer...3"
        }
        login_response = requests.post(url, data=login_payload)
        if login_response.status_code == 200:
            login_data = login_response.json()
            auth_data = login_data['data']['auth_data']

            url = "https://www.maomaovpn.com/api/v1/user/getSubscribe"
            headers = {
                "Authorization": auth_data
            }
            subscription_response = requests.get(url, headers=headers)
            if subscription_response.status_code == 200:
                json_response = subscription_response.json()
                subscribe_url = json_response.get('data', {}).get('subscribe_url')
                print(subscribe_url)
                with open(subscribe_file_path, "a") as file:
                    file.write(subscribe_url + "\n")
            else:
                print("Failed to retrieve subscription URL.")
        else:
            print("Login failed for", next_email)
    else:
        print("No verification code found.")

    if _ < iteration_count - 1:
        print(f"Waiting for 5 seconds before the next iteration...")
        time.sleep(5)

