from src.client import IMAPClient, ConnectionErr, LoginErr, MailboxErr
from pytest import raises
from unittest.mock import Mock


class TestClient:
    def test_connection_err(self):
        client = IMAPClient()

        with raises(ConnectionErr):
            client.login("", "")
        with raises(ConnectionErr):
            client.list_mailboxes()
        with raises(ConnectionErr):
            client.select_mailbox("")
        with raises(ConnectionErr):
            list(client.list_emails())  # list необходим, чтобы метод начал выполняться
        with raises(ConnectionErr):
            client.read_email(0)
        with raises(ConnectionErr):
            client.download_attachments("", "")
        with raises(ConnectionErr):
            client.upload_email("", "", "")

    def test_login_err(self):
        client = IMAPClient()
        client._connection = "connectionImitation"  # имитация того, что подключение есть

        with raises(LoginErr):
            client.list_mailboxes()
        with raises(LoginErr):
            client.select_mailbox("")
        with raises(LoginErr):
            list(client.list_emails())  # list необходим, чтобы метод начал выполняться
        with raises(LoginErr):
            client.read_email(0)
        with raises(LoginErr):
            client.download_attachments("", "")
        with raises(LoginErr):
            client.upload_email("", "", "")

    def test_mailbox_err(self):
        client = IMAPClient()
        client._connection = "connectionImitation"  # имитация того, что подключение есть
        client._logged_in = True

        with raises(MailboxErr):
            list(client.list_emails())  # list необходим, чтобы метод начал выполняться
        with raises(MailboxErr):
            client.read_email(0)
        with raises(MailboxErr):
            client.download_attachments("", "")

    def test_connection_impossible(self):
        client = IMAPClient()

        with raises(Exception):
            client.connect("", 993, 2)
        with raises(Exception):
            client.connect_ssl("", 993, 2)

    def test_list_mailboxes(self):
        client = IMAPClient()
        client._logged_in = True
        client._connection = Mock()
        client._connection.list.return_value = ("OK", [b"(\\noselect)\"1\"", b"\"2\"", b"\"3\""])

        assert list(client.list_mailboxes()) == ["2", "3"]

        client._connection.list.return_value = ("NO", [])

        assert client.list_mailboxes() is None

    def test_select_mailbox(self):
        client = IMAPClient()
        client._logged_in = True
        client._connection = Mock()
        client._connection.select.return_value = ("OK", "")

        assert client.select_mailbox("1") == ("OK", "")
        assert client._mailbox_selected

        client._connection.select.return_value = ("NO", "")
        client._mailbox_selected = False

        assert client.select_mailbox("1") == ("NO", "")
        assert not client._mailbox_selected

    def test_read_email(self):
        client = IMAPClient()
        client._logged_in = True
        client._mailbox_selected = True
        client._connection = Mock()
        client._connection.fetch.return_value = ("NO", [])

        assert client.read_email(0) is None

        client._connection.fetch.return_value = ("OK", [(b"Bad", b"Content-Type: multipart\nGood")])
        res = client.read_email(0)

        assert res is not None
        assert res.body == ["Good"]

        client._connection.fetch.return_value = ("OK", [(b"Bad", b"Content-Type: text/html\nGood")])
        res = client.read_email(0)

        assert res is not None
        assert res.body == ["Good"]

    def test_upload_email(self):
        client = IMAPClient()
        client._logged_in = True
        client._login = "login"
        client._connection = Mock()

        client.upload_email("", "", "")

        client._connection.append.assert_called_once()

    def test_close(self):
        client = IMAPClient()
        client._logged_in = True
        client._login = "login"
        client._password = "password"
        client._connection = Mock()

        client.close()

        assert not client._logged_in
        assert not client._connection
        assert not client._mailbox_selected
        assert client._login == ""
        assert client._password == ""

    def test_bad_download_attachments(self):
        client = IMAPClient()
        client._logged_in = True
        client._mailbox_selected = True
        client._connection = Mock()
        msg_mock = Mock()
        client._connection.fetch.return_value = ("NO", msg_mock)

        assert client.download_attachments("", "") is None

        msg_mock.assert_not_called()
