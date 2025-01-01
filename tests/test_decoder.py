from src.decoder import imaputf7decode, imaputf7encode


class TestDecoder:
    def test_imaputf7decode(self):
        assert imaputf7decode("&BBIEMAQ2BD0EPgQ1-") == "Важное"
        assert imaputf7decode("&BBIEQQRP- &BD8EPgRHBEIEMA-") == "Вся почта"
        assert imaputf7decode("&BBoEPgRABDcEOAQ9BDA-") == "Корзина"
        assert imaputf7decode("&BB4EQgQ,BEAEMAQyBDsENQQ9BD0ESwQ1-") == "Отправленные"
        assert imaputf7decode("&BB8EPgQ8BDUERwQ1BD0EPQRLBDU-") == "Помеченные"
        assert imaputf7decode("&BCEEPwQwBDw-") == "Спам"
        assert imaputf7decode("&BCcENQRABD0EPgQyBDgEOgQ4-") == "Черновики"

    def test_imaputf7encode(self):
        assert "&BBIEMAQ2BD0EPgQ1-" == imaputf7encode("Важное")
        assert "&BBIEQQRP- &BD8EPgRHBEIEMA-" == imaputf7encode("Вся почта")
        assert "&BBoEPgRABDcEOAQ9BDA-" == imaputf7encode("Корзина")
        assert "&BB4EQgQ/BEAEMAQyBDsENQQ9BD0ESwQ1-" == imaputf7encode("Отправленные")
        assert "&BB8EPgQ8BDUERwQ1BD0EPQRLBDU-" == imaputf7encode("Помеченные")
        assert "&BCEEPwQwBDw-" == imaputf7encode("Спам")
        assert "&BCcENQRABD0EPgQyBDgEOgQ4-" == imaputf7encode("Черновики")
