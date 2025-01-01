import getpass
from src.client import IMAPClient, MailboxErr, LoginErr

if __name__ == "__main__":
    while True:
        server = input("Введите сервер IMAP: ")
        port = int(input("Введите порт IMAP (993): "))
        use_ssl = input("Использовать SSL? (y/n): ").strip().lower() == "y"

        client = IMAPClient()
        try:
            if use_ssl:
                client.connect_ssl(server, port if port else 993)
            else:
                client.connect(server, port if port else 993)
            break
        except Exception as e:
            print(f"Ошибка {e}")

    while True:
        try:
            username = input("Введите логин: ")
            password = getpass.getpass("Введите пароль: ")
            client.login(username, password)
            break
        except Exception as e:
            print(f"Ошибка: {e}")

    while True:
        print("\nДоступные команды:")
        print("1. Список папок")
        print("2. Выбрать папку")
        print("3. Список писем")
        print("4. Прочитать письмо")
        print("5. Скачать вложения")
        print("6. Загрузить письмо")
        print("7. Выход\n")

        choice = input("Выберите команду: ").strip()
        if choice == "1":
            for mailbox in client.list_mailboxes():
                print(mailbox)
        elif choice == "2":
            mailbox = input("Введите название папки из списка: ")
            res = client.select_mailbox(mailbox)
            if res[0].casefold() == "ok":
                print(f"Вы выбрали папку {mailbox}")
            else:
                print("Ошибка")
        elif choice == "3":
            try:
                i = 0
                more = True
                for email in client.list_emails():
                    if not more:
                        break
                    i += 1
                    body = client.read_email(email[0])
                    joined_body = " ".join(body).replace("\n", " ")
                    print(
                        "Id письма: "
                        + "    ".join(email)
                        + "    "
                        + joined_body[: min(20, len(joined_body))]
                        + "..."
                    )
                    if i >= 10:
                        i = 0
                        more = input("Загрузить ещё? (y/n): ").strip().lower() == "y"
            except MailboxErr as e:
                print(f"Ошибка: {e}")
        elif choice == "4":
            try:
                email_id = input("Введите ID письма: ")
                print("\n".join(client.read_email(email_id)))
            except MailboxErr as e:
                print(f"Ошибка: {e}")
        elif choice == "5":
            try:
                email_id = input("Введите ID письма: ")
                path = input("Введите путь для сохранения вложений: ")
                client.download_attachments(email_id, path)
            except MailboxErr as e:
                print(f"Ошибка: {e}")
        elif choice == "6":
            try:
                subject = input("Введите тему письма: ")
                body = input("Введите тело письма: ")
                recipient = input("Введите адрес получателя: ")
                client.upload_email(subject, body, recipient)
            except LoginErr as e:
                print(f"Ошибка: {e}")
        elif choice == "7":
            client.close()
            break
        else:
            print("Неверная команда.")
