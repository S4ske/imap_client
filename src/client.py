import imaplib
import email
from email.header import decode_header
import os
import time


class IMAPClient:
    def __init__(self, server, port, use_ssl=True):
        self.server = server
        self.port = port
        self.use_ssl = use_ssl
        self.connection = None

    def connect(self):
        """Устанавливает соединение с сервером."""
        try:
            if self.use_ssl:
                self.connection = imaplib.IMAP4_SSL(self.server, self.port)
            else:
                self.connection = imaplib.IMAP4(self.server, self.port)
            print(f"Подключено к серверу {self.server}:{self.port}")
        except Exception as e:
            print(f"Ошибка подключения: {e}")

    def login(self, username, password):
        """Выполняет аутентификацию пользователя."""
        try:
            self.connection.login(username, password)
            print("Аутентификация успешна!")
        except Exception as e:
            print(f"Ошибка аутентификации: {e}")

    def list_mailboxes(self):
        """Выводит список доступных папок."""
        try:
            status, mailboxes = self.connection.list()
            if status == "OK":
                print("Доступные папки:")
                for mailbox in mailboxes:
                    print(mailbox.decode())
            else:
                print("Не удалось получить список папок.")
        except Exception as e:
            print(f"Ошибка получения папок: {e}")

    def select_mailbox(self, mailbox):
        """Выбирает папку для работы."""
        try:
            self.connection.select(mailbox)
            print(f"Папка '{mailbox}' выбрана.")
        except Exception as e:
            print(f"Ошибка выбора папки: {e}")

    def list_emails(self):
        """Показывает список писем с отправителем, темой и первыми символами."""
        try:
            status, messages = self.connection.search(None, "ALL")
            if status != "OK":
                print("Не удалось получить письма.")
                return

            email_ids = messages[0].split()
            print(f"Найдено писем: {len(email_ids)}")

            for email_id in email_ids:
                status, msg_data = self.connection.fetch(email_id, "(RFC822)")
                if status != "OK":
                    print(f"Ошибка чтения письма {email_id.decode()}")
                    continue

                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding or "utf-8")
                        sender = msg.get("From")
                        print(f"ID: {email_id.decode()}, Отправитель: {sender}, Тема: {subject}")
        except Exception as e:
            print(f"Ошибка просмотра писем: {e}")

    def read_email(self, email_id):
        """Просмотр письма с обработкой кодировок."""
        try:
            status, msg_data = self.connection.fetch(email_id, "(RFC822)")
            if status != "OK":
                print(f"Не удалось загрузить письмо {email_id.decode()}")
                return

            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding or "utf-8")
                    print(f"Тема: {subject}")
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition"))
                            if content_type == "text/plain" and "attachment" not in content_disposition:
                                body = part.get_payload(decode=True)
                                print("Тело письма:", body.decode(part.get_content_charset() or "utf-8"))
                    else:
                        body = msg.get_payload(decode=True)
                        print("Тело письма:", body.decode(msg.get_content_charset() or "utf-8"))
        except Exception as e:
            print(f"Ошибка чтения письма: {e}")

    def download_attachments(self, email_id, download_path):
        """Скачивает все вложения письма."""
        try:
            status, msg_data = self.connection.fetch(email_id, "(RFC822)")
            if status != "OK":
                print(f"Не удалось загрузить письмо {email_id.decode()}")
                return

            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    for part in msg.walk():
                        if part.get_content_maintype() == "multipart":
                            continue
                        if part.get("Content-Disposition") is None:
                            continue
                        filename = part.get_filename()
                        if filename:
                            filepath = os.path.join(download_path, filename)
                            with open(filepath, "wb") as f:
                                f.write(part.get_payload(decode=True))
                            print(f"Вложение {filename} сохранено в {filepath}")
        except Exception as e:
            print(f"Ошибка скачивания вложений: {e}")

    def upload_email(self, mailbox, subject, body, recipient):
        """Загружает письмо на сервер."""
        try:
            msg = email.message.EmailMessage()
            msg["From"] = "me@example.com"  # Замените на реальный адрес
            msg["To"] = recipient
            msg["Subject"] = subject
            msg.set_content(body)
            self.connection.append(mailbox, "", imaplib.Time2Internaldate(time.time()), msg.as_bytes())
            print("Письмо успешно загружено.")
        except Exception as e:
            print(f"Ошибка загрузки письма: {e}")

    def close(self):
        """Закрывает соединение."""
        if self.connection:
            self.connection.logout()
            print("Соединение закрыто.")
