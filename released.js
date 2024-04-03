const fs = require('fs');
const path = require('path');
const axios = require('axios');
const Imap = require('imap');
const simpleParser = require('mailparser').simpleParser;

const EMAIL = 'your-email-must-is@outlook.com';
const PASSWORD = 'your-outlook-password';
const SERVER = 'imap-mail.outlook.com';

const appDataPath = process.env.APPDATA;
const maomaoFolderPath = path.join(appDataPath, 'Maomao');
if (!fs.existsSync(maomaoFolderPath)) {
    fs.mkdirSync(maomaoFolderPath, { recursive: true });
}
const statusFilePath = path.join(maomaoFolderPath, 'email_status.txt');

function loadCurrentStatus() {
    if (fs.existsSync(statusFilePath)) {
        return fs.readFileSync(statusFilePath, 'utf8').trim();
    } else {
        return 'a00';
    }
}

function saveCurrentStatus(status) {
    fs.writeFileSync(statusFilePath, status, 'utf8');
}

function getNextStatus(currentStatus) {
    let letter = currentStatus[0];
    let number = parseInt(currentStatus.substring(1), 10) + 1;
    if (number > 99) {
        number = 1;
        letter = String.fromCharCode(letter.charCodeAt(0) + 1);
    }
    return `${letter}${number.toString().padStart(2, '0')}`;
}

function generateNextEmail(baseEmail) {
    const currentStatus = loadCurrentStatus();
    const nextStatus = getNextStatus(currentStatus);
    saveCurrentStatus(nextStatus);
    const parts = baseEmail.split('@');
    return `${parts[0]}+${nextStatus}@${parts[1]}`;
}

async function sendVerificationRequest(email) {
    const url = "https://www.maomaovpn.com/api/v1/passport/comm/sendEmailVerify";
    const payload = { email };
    const headers = {
        "Content-Type": "application/json",
        "Referrer-Policy": "strict-origin-when-cross-origin"
    };
    const response = await axios.post(url, payload, { headers });
    console.log(response.data);
}

const baseEmail = "maomaocloud2024@outlook.com";
const nextEmail = generateNextEmail(baseEmail);
console.log("使用的email:", nextEmail);

sendVerificationRequest(nextEmail);

setTimeout(() => {
    const imap = new Imap({
        user: EMAIL,
        password: PASSWORD,
        host: SERVER,
        port: 993,
        tls: true
    });

    function openInbox(cb) {
        imap.openBox('INBOX', true, cb);
    }

    imap.once('ready', () => {
        openInbox((err, box) => {
            if (err) throw err;
            const searchCriteria = ['UNSEEN'];
            const fetchOptions = { bodies: '', markSeen: true };
            imap.search(searchCriteria, (err, results) => {
                if (err) throw err;
                if (results.length > 0) {
                    const f = imap.fetch(results, fetchOptions);
                    f.on('message', (msg, seqNo) => {
                        msg.on('body', (stream) => {
                            simpleParser(stream, async (err, parsed) => {
                                if (err) throw err;
                                if (parsed.subject === '猫猫云邮箱验证码') {
                                    const match = parsed.text.match(/\b\d{6}\b/);
                                    if (match) {
                                        console.log('验证码:', match[0]);
                                        // Continue with registration process using the verification code
                                        const registrationData = {
                                            "email": nextEmail,
                                            "password": "Qwer...3",
                                            "invite_code": "invite_code_here_if_u_need",
                                            "email_code": match[0]
                                        };
                                        const response = await axios.post("https://www.maomaovpn.com/api/v1/passport/auth/register", registrationData);
                                        console.log(response.data);
                                    }
                                }
                            });
                        });
                    });
                    f.once('error', (err) => {
                        console.log('Fetch error: ' + err);
                    });
                    f.once('end', () => {
                        console.log('Done fetching all messages!');
                        imap.end();
                    });
                } else {
                    console.log('No new messages to process');
                    imap.end();
                }
            });
        });
    });

    imap.once('error', (err) => {
        console.log(err);
    });

    imap.once('end', () => {
        console.log('Connection ended');
    });

    imap.connect();
}, 15000);
