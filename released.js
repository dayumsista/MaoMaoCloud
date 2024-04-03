const fs = require('fs');
const path = require('path');
const axios = require('axios');
const Imap = require('node-imap');
const { simpleParser } = require('mailparser');
const util = require('util');
const sleep = util.promisify(setTimeout);

const EMAIL = 'your_email_must_is@outlook.com';
const PASSWORD = 'ur_outlook_acc_passw';
const SERVER = 'imap-mail.outlook.com';

const appdataPath = process.env.APPDATA;
const maomaoFolderPath = path.join(appdataPath, 'Maomao');
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
  fs.writeFileSync(statusFilePath, status);
}

function getNextStatus(currentStatus) {
  let letter = currentStatus.charAt(0),
      number = parseInt(currentStatus.substring(1), 10) + 1;
  if (number > 99) {
    number = 1;
    letter = String.fromCharCode(letter.charCodeAt(0) + 1);
  }
  return `${letter}${('0' + number).slice(-2)}`;
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

const baseEmail = "base_email_should_same_with_your@outlook.com";
const nextEmail = generateNextEmail(baseEmail);
console.log("using_email:", nextEmail);

(async () => {
  await sendVerificationRequest(nextEmail);
  console.log("wait 15...");
  await sleep(15000);

  // IMAP operations, email fetching, and further actions would follow here
  // Due to the complexity and the requirement of specific libraries, detailed implementations for IMAP operations are not provided here.
  // However, you would use the `node-imap` library to connect, fetch, and parse emails, similar to the Python script's functionality.

  // Placeholder for IMAP login and email fetching
  console.log("IMAP operations would be implemented here");

  // Further processing based on fetched emails would also follow
})();

