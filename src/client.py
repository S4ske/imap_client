import imaplib
import email
from email.message import EmailMessage, Message
from email.header import decode_header
import os
import time
from typing import Literal, Any, Iterable
import re
from src.decoder import imaputf7decode, imaputf7encode
from bs4 import BeautifulSoup
from src.email_model import Email


class ConnectionErr(Exception):
    pass


class LoginErr(Exception):
    pass


class MailboxErr(Exception):
    pass


class IMAPClient:
    def __init__(self) -> None:
        self._connection: imaplib.IMAP4 | None = None
        self._logged_in = False
        self._mailbox_selected = False
        self._login = ""
        self._password = ""

    def connect(self, server: str, port: int = 993, timeout: int = 5) -> None:
        self._connection = imaplib.IMAP4_SSL(server, port, timeout=timeout)

    def connect_ssl(self, server: str, port: int = 993, timeout: int = 5) -> None:
        self._connection = imaplib.IMAP4_SSL(server, port, timeout=timeout)

    def _check_connection(self) -> None:
        if not self._connection:
            raise ConnectionErr("Необходимо подключиться к серверу")

    def login(self, username: str, password: str) -> (Literal["OK"], Any):
        self._check_connection()
        res = self._connection.login(username, password)
        self._logged_in = True
        self._login = username
        self._password = password
        return res

    def _check_logged_in(self) -> None:
        self._check_connection()
        if not self._logged_in:
            raise LoginErr("Необходимо авторизоваться")

    def list_mailboxes(self) -> list[str] | None:
        self._check_logged_in()
        status, mailboxes = self._connection.list()
        if status == "OK":
            return self._parse_mailboxes(mailboxes)
        else:
            return None

    @staticmethod
    def _parse_mailboxes(mailboxes: list[None] | list[bytes | tuple[bytes, bytes]]) -> list[str]:
        res = []
        for mailbox in map(lambda x: x.decode("utf-8", errors="ignore"), mailboxes):
            parsed_mailbox = IMAPClient._parse_mailbox(mailbox)
            if parsed_mailbox:
                res.append(parsed_mailbox)
        return res

    @staticmethod
    def _parse_mailbox(mailbox: str) -> str | None:
        if "\\noselect" in mailbox.casefold():
            return
        return imaputf7decode(mailbox.split('"')[-2])

    def select_mailbox(self, mailbox: str) -> (str, Any):
        self._check_logged_in()
        res = self._connection.select(self._encode_mailbox_utf7(mailbox))
        if res[0].casefold() == "ok":
            self._mailbox_selected = True
        return res

    @staticmethod
    def _encode_mailbox_utf7(mailbox: str) -> str:
        mailbox_imap = []
        for component in mailbox.split("/"):
            mailbox_imap += [imaputf7encode(component).replace("/", ",")]
        return "/".join(mailbox_imap)

    def _check_mailbox_selected(self) -> None:
        self._check_logged_in()
        if not self._mailbox_selected:
            raise MailboxErr("Необходимо выбрать папку")

    def list_emails(self, reverse: bool = True) -> Iterable[Email]:
        self._check_mailbox_selected()
        status, messages = self._connection.search(None, "ALL")
        if status != "OK":
            raise StopIteration
        yield from self._build_emails(messages, reverse)

    def _build_emails(self, messages: list, reverse: bool = True) -> Iterable[Email]:
        email_ids = messages[0].split()

        for email_id in email_ids[::-1] if reverse else email_ids:
            yield self.read_email(email_id)

    @staticmethod
    def _get_body(message: Message) -> list[str]:
        content_type = message.get_content_type()
        if content_type == "multipart/alternative":
            return []
        content_disposition = str(message.get("Content-Disposition"))
        if "attachment" in content_disposition:
            return [IMAPClient._get_decoded_filename(message)]
        if "multipart" in content_type:
            res = []
            for part in list(message.walk())[1:]:
                res.extend(IMAPClient._get_body(part))
            return res
        if content_type == "text/plain" and "attachment" not in content_disposition:
            return [IMAPClient._get_decoded_text_plain(message)]
        elif content_type == "text/html" and "attachment" not in content_disposition:
            return [IMAPClient._get_decoded_text_html(message)]
        return []

    @staticmethod
    def _get_decoded_text_plain(message: Message) -> str:
        raw_payload = message.get_payload(decode=True)
        encoding = message.get_content_charset()
        if not encoding or encoding == "unknown-8bit":
            encoding = "utf-8"
        return raw_payload.decode(encoding, errors="ignore")

    @staticmethod
    def _get_decoded_text_html(message: Message) -> str:
        encoding = message.get_content_charset()
        if not encoding or encoding == "unknown-8bit":
            encoding = "utf-8"
        html_body = message.get_payload(decode=True).decode(
            encoding, errors="ignore"
        )
        soup = BeautifulSoup(html_body, "html.parser")
        return soup.get_text()

    def read_email(self, email_id: int) -> Email | None:
        self._check_mailbox_selected()
        status, message_data = self._connection.fetch(str(email_id), "(RFC822)")
        if status != "OK":
            return None
        return self._create_email_from_bytes(email_id, message_data)

    @staticmethod
    def _create_email_from_bytes(email_id: int, message_data:  list[None] | list[bytes | tuple[bytes, bytes]]) -> Email:
        for message_part in message_data:
            if IMAPClient._message_part_is_data(message_part):
                return IMAPClient._create_email_from_data(email_id, message_part[1])

    @staticmethod
    def _create_email_from_data(email_id: int, data: bytes) -> Email:
        msg = email.message_from_bytes(data)
        return Email(email_id,
                     IMAPClient._get_sender(msg),
                     IMAPClient._get_decoded_email_part(msg, "Subject"),
                     IMAPClient._get_body(msg))

    @staticmethod
    def _get_decoded_email_part(message: Message, part: str) -> str | None:
        raw_part = message.get(part)
        part, encoding = decode_header(raw_part)[0] if raw_part else (None, None)
        if not encoding or encoding == "unknown-8bit":
            encoding = "utf-8"
        if isinstance(part, bytes):
            part = part.decode(encoding, errors="ignore")
        return part

    @staticmethod
    def _get_sender(message: Message) -> str | None:
        sender = IMAPClient._get_decoded_email_part(message, "From")
        if not sender:
            return None
        re_sender = re.search(r"<(.*)>", sender)
        if re_sender:
            return re_sender.group(1)
        return sender

    @staticmethod
    def _message_part_is_data(message_part: Any) -> bool:
        return isinstance(message_part, tuple)

    def download_attachments(self, email_id: str, download_path: str) -> None:
        self._check_mailbox_selected()
        status, msg_data = self._connection.fetch(email_id, "(RFC822)")
        if status != "OK":
            return

        for response_part in msg_data:
            if self._message_part_is_data(response_part):
                self._download_attachments_from_data(response_part[1], download_path)

    @staticmethod
    def _download_attachments_from_data(data: bytes, download_path: str) -> None:
        msg = email.message_from_bytes(data)
        for part in msg.walk():
            if part.get_content_maintype() == "multipart":
                continue
            if "attachment" not in str(part.get("Content-Disposition")):
                continue
            filename = IMAPClient._get_decoded_filename(part)
            if filename:
                IMAPClient._download_file_from_email(part, filename, download_path)

    @staticmethod
    def _download_file_from_email(message: Message, filename: str, download_path: str) -> None:
        filepath = os.path.join(download_path, filename)
        with open(filepath, "wb") as f:
            f.write(message.get_payload(decode=True))

    @staticmethod
    def _get_decoded_filename(message: Message) -> str | None:
        raw_filename = message.get_filename()
        filename, encoding = decode_header(raw_filename)[0]
        if not encoding or encoding == "unknown-8bit":
            encoding = "utf-8"
        if isinstance(filename, bytes):
            filename = filename.decode(encoding, errors="ignore")
        return filename

    def upload_email(self, subject: str, body: str, recipient: str) -> None:
        self._check_logged_in()
        msg = EmailMessage()
        msg["From"] = self._login
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.set_content(body)
        self._connection.append(
            "INBOX", "", imaplib.Time2Internaldate(time.time()), msg.as_bytes()
        )

    def close(
        self,
    ) -> None | tuple[str, list[None] | list[bytes | tuple[bytes, bytes]]]:
        self._logged_in = False
        self._login = ""
        self._password = ""
        self._mailbox_selected = False
        if self._connection:
            res = self._connection.logout()
            self._connection = None
            return res
