import tuxrun.__main__
from tuxrun.__main__ import start, main


def test_start_calls_main(monkeypatch, mocker):
    monkeypatch.setattr(tuxrun.__main__, "__name__", "__main__")
    main = mocker.patch("tuxrun.__main__.main")
    start()
    main.assert_called()


def test_main():
    main()
