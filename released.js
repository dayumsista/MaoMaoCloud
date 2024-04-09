require('dotenv').config();
const fs = require('fs-extra');
const path = require('path');
const fetch = require('node-fetch');
const Imap = require('node-imap');
const { simpleParser } = require('mailparser');

const EMAIL = process.env.EMAIL;
const PASSWORD = process.env.PASSWORD;
const SERVER = process.env.SERVER || 'imap-mail.outlook.com';
const DESIRED_SUBJECT = '猫猫云邮箱验证码';
const BASE_EMAIL = process.env.BASE_EMAIL;
const APPDATA_PATH = process.env.APPDATA || '.';
const MAOMAO_FOLDER_PATH = path.join(APPDATA_PATH, 'Maomao');
const STATUS_FILE_PATH = path.join(MAOMAO_FOLDER_PATH, 'email_status.txt');
const SUBSCRIBE_FILE_PATH = path.join(MAOMAO_FOLDER_PATH, 'subscribe_url.txt');

async function ensureEnvironment() {
    await fs.ensureDir(MAOMAO_FOLDER_PATH);
    if (!await fs.exists(STATUS_FILE_PATH)) {
        await fs.writeFile(STATUS_FILE_PATH, 'a00');
    }
}

async function loadCurrentStatus() {
    const data = await fs.readFile(STATUS_FILE_PATH, 'utf8');
    return data.trim();
}

async function saveCurrentStatus(status) {
    await fs.writeFile(STATUS_FILE_PATH, status);
}

function nextStatus(currentStatus) {
    let [letter, number] = [currentStatus.slice(0, 1), parseInt(currentStatus.slice(1))];
    number++;
    if (number > 99) {
        number = 0;
        letter = String.fromCharCode(letter.charCodeAt(0) + 1);
    }
    return `${letter}${number.toString().padStart(2, '0')}`;
}

function generateNextEmail(baseEmail, currentStatus) {
    const parts = baseEmail.split('@');
    return `${parts[0]}+${nextStatus(currentStatus)}@${parts[1]}`;
}

async function sendVerificationRequest(email) {
    const url = "https://www.maomaovpn.com/api/v1/passport/comm/sendEmailVerify";
    const response = await fetch(url, {
        method: 'POST',
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email })
    });
    console.log('Verification request sent, response:', await response.json());
}

async function getVerificationCode(imap, searchCriteria, fromEmail) {
    return new Promise((resolve, reject) => {
        imap.once('ready', () => {
            imap.openBox('INBOX', false, async (err) => {
                if (err) reject(err);
                imap.search([['FROM', fromEmail], ['SUBJECT', DESIRED_SUBJECT], ['UNSEEN']], (err, results) => {
                    if (err || !results.length) {
                        console.log('No unread emails with the desired subject.');
                        resolve(null);
                        return;
                    }

                    const f = imap.fetch(results, { bodies: 'TEXT' });
                    f.on('message', (msg) => {
                        msg.on('body', (stream) => {
                            simpleParser(stream, (err, parsed) => {
                                if (err) {
                                    reject(err);
                                    return;
                                }
                                const match = parsed.text.match(/\b\d{6}\b/);
                                if (match) {
                                    resolve(match[0]);
                                }
                            });
                        });
                    });
                    f.once('error', (err) => reject(err));
                    f.once('end', () => {
                        console.log('Done fetching emails.');
                        imap.end();
                    });
                });
            });
        });
        imap.connect();
    });
}

async function fetchVerificationCode(email) {
    const imap = new Imap({
        user: EMAIL,
        password: PASSWORD,
        host: SERVER,
        port: 993,
        tls: true
    });

    try {
        const code = await getVerificationCode(imap, ['UNSEEN', ['SUBJECT', DESIRED_SUBJECT]], email);
        return code;
    } catch (error) {
        console.error('Error fetching verification code:', error);
        throw error;
    }
}

async function registerAccount(email, verificationCode) {
    const registrationUrl = "https://www.maomaovpn.com/api/v1/passport/auth/register";
    const registrationData = {
        email: email,
        password: "Qwer...@3", 
        invite_code: "YSirkEU4", 
        email_code: verificationCode
    };

    const response = await fetch(registrationUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(registrationData)
    });

    if (response.ok) {
        console.log('Registration successful');
    } else {
        const error = await response.text();
        console.error('Registration failed:', error);
    }
}

async function main() {
    await ensureEnvironment();
    const currentStatus = await loadCurrentStatus();
    const nextEmail = generateNextEmail(BASE_EMAIL, currentStatus);
    await saveCurrentStatus(nextStatus(currentStatus));
    console.log(`Using email: ${nextEmail}`);

    await sendVerificationRequest(nextEmail);

    // Adjust delay as needed to ensure the email has time to arrive
    await new Promise(resolve => setTimeout(resolve, 20000)); 

    const verificationCode = await fetchVerificationCode(nextEmail);
    if (verificationCode) {
        console.log(`Verification code received: ${verificationCode}`);
        await registerAccount(nextEmail, verificationCode);
        // Additional logic for logging in and fetching subscription URL can go here
    } else {
        console.log('No verification code received.');
    }
}

main().catch(console.error);

