import os
import imaplib
import email
from email.header import decode_header
import re
import requests
import time

EMAIL = base_email = 'email@outlook.com'#这里放你的outlook邮箱
PASSWORD = 'password@1234'#outlook邮箱密码
SERVER = 'imap-mail.outlook.com'
password = 'Qwer...@3'
desired_subject = '猫猫云邮箱验证码'
invite_code = 'invite_code'#该网站邀请码

appdata_path = os.environ.get('APPDATA')
maomao_folder_path = os.path.join(appdata_path, 'Maomao')
if not os.path.exists(maomao_folder_path):
    os.makedirs(maomao_folder_path)
status_file_path = os.path.join(maomao_folder_path, 'email_status.txt')
subscribe_file_path = os.path.join(maomao_folder_path, 'subscribe_url.txt')

def load_current_status():
    if os.path.exists(status_file_path):
        with open(status_file_path, 'r') as file:
            return file.read().strip()
    return 'a00'

def save_current_status(status):
    with open(status_file_path, 'w') as file:
        file.write(status)

def get_next_status(current_status):
    letter, number = current_status[0], int(current_status[1:])
    number += 1
    if number > 99:
        number = 1
        next_letter = chr(ord(letter) + 1) if letter != 'Z' else 'A'
        letter = next_letter
    next_status = f'{letter}{number:02d}'
    return next_status

def generate_next_email(base_email):
    current_status = load_current_status()
    next_status = get_next_status(current_status)
    save_current_status(next_status)
    parts = base_email.split('@')
    return f"{parts[0]}+{next_status}@{parts[1]}", next_status

def send_verification_request(email):
    url = "https://maomao.cloud/api/v1/passport/comm/sendEmailVerify"
    payload = {"email": email}
    headers = {
        "Content-Type": "application/json",
        "Referrer-Policy": "strict-origin-when-cross-origin"
    }
    response = requests.post(url, json=payload, headers=headers)
    print(response)

def connect_to_mailbox(mail, folder):
    mail.select(f'"{folder}"')
    status, messages = mail.search(None, '(UNSEEN)')
    return status, messages

def fetch_email(mail, mail_id):
    status, data = mail.fetch(mail_id, '(RFC822)')
    return status, data

def parse_email(data):
    for response_part in data:
        if isinstance(response_part, tuple):
            return email.message_from_bytes(response_part[1])
    return None

def get_subject(msg):
    subject = decode_header(msg["subject"])[0][0]
    if isinstance(subject, bytes):
        subject = subject.decode()
    return subject

def extract_verification_code(msg):
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() in ["text/plain", "text/html"]:
                return extract_code_from_body(part.get_payload(decode=True).decode())
    else:
        return extract_code_from_body(msg.get_payload(decode=True).decode())

def extract_code_from_body(email_body):
    match = re.search(r"\b\d{6}\b", email_body)
    if match:
        return match.group(0)
    return None

def process_emails(mail, folders, desired_subject):
    emails_info = {}
    for folder in folders:
        status, messages = connect_to_mailbox(mail, folder)
        if status == 'OK':
            emails_info[folder] = []
            for mail_id in messages[0].split():
                status, data = fetch_email(mail, mail_id)
                msg = parse_email(data)
                if msg and get_subject(msg) == desired_subject:
                    verification_code = extract_verification_code(msg)
                    if verification_code:
                        emails_info[folder].append({'Subject': desired_subject, '验证码': verification_code})
    return emails_info

iteration_count = int(input("线程循环执行次数: "))

def get_user_confirmation(prompt):
    while True:
        user_input = input(f"{prompt} (Yes or No): ").strip()
        if user_input.lower() == "yes":
            return True
        elif user_input.lower() == "no":
            return False
        else:
            print("无效输入，请只输入 'Yes' 或 'No'.")
            
Download = get_user_confirmation("是否下载Clash参数文件")
Config = get_user_confirmation("是否要导入参数文件到Clash")

for _ in range(iteration_count):
    next_email, next_status = generate_next_email(base_email)  
    print("使用的email:", next_email)

    send_verification_request(next_email)
    print("等待10秒...")
    time.sleep(10)

    mail = imaplib.IMAP4_SSL(SERVER)
    mail.login(EMAIL, PASSWORD)
    folders = ['inbox', 'Junk']
    emails_info = process_emails(mail, folders, desired_subject)
    print(emails_info)

    for folder in folders:
        mail.select(f'"{folder}"', readonly=False)
        status, messages = mail.search(None, 'ALL')
        if status == 'OK':
            for mail_id in messages[0].split():
                mail.store(mail_id, '+FLAGS', '\\Deleted')
            mail.expunge()

    mail.logout()

    if emails_info:
        for folder in folders:
            if folder in emails_info and emails_info[folder]:
                for email_info in emails_info[folder]:
                    verification_code = email_info['验证码']
                    print("code found:", verification_code)

                    registration_data = {
                        "email": next_email,
                        "password": password,
                        "invite_code": "YSirkEU4",
                        "email_code": verification_code
                    }

                    url = "https://maomao.cloud/api/v1/passport/auth/register"
                    response = requests.post(url, data=registration_data)
                    print(response)
                    if response.status_code == 500:
                        print("注册请求失败，正在退出...")
                        break

                    time.sleep(5)

                    url = "https://maomao.cloud/api/v1/passport/auth/login"
                    login_payload = {
                        "email": next_email,
                        "password": password
                    }
                    login_response = requests.post(url, data=login_payload)
                    if login_response.status_code == 200:
                        login_data = login_response.json()
                        auth_data = login_data['data']['auth_data']

                        url = "https://maomao.cloud/api/v1/user/getSubscribe"
                        headers = {"Authorization": auth_data}
                        subscription_response = requests.get(url, headers=headers)
                        if subscription_response.status_code == 200:
                            json_response = subscription_response.json()
                            subscribe_url = json_response.get('data', {}).get('subscribe_url')
                            print(subscribe_url)
                            with open(subscribe_file_path, "a") as file:
                                file.write(subscribe_url + "\n")
                            if Download:
                                download_url = subscribe_url + "&flag=clash"
                                maomao_folder_path = os.path.join(appdata_path, 'Maomao')
                                response = requests.get(download_url)
                                file_path = os.path.join(maomao_folder_path, next_status)
                                with open(file_path, 'wb') as f:
                                    f.write(response.content)
                                print("成功下载")
                            if Config:
                                run_command = f"start clash://install-config?url={subscribe_url}"
                                os.system(run_command)
                                print("成功导入")
                        else:
                            print("获取URL失败.")
                    else:
                        print("登录失败", next_email)
            else:
                print(f"在{folder}中未找到验证码.")
    else:
        print("全部信箱文件夹中都未找到验证码.")

    if _ < iteration_count - 1:
        print(f"在下一个线程开始前等待五秒...")
        time.sleep(5)
