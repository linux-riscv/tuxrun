import pytest

import tuxrun.__main__
from tuxrun.__main__ import start, main


def test_start_calls_main(monkeypatch, mocker):
    monkeypatch.setattr(tuxrun.__main__, "__name__", "__main__")
    main = mocker.patch("tuxrun.__main__.main")
    with pytest.raises(SystemExit):
        start()
    main.assert_called()


def test_main_usage(capsys):
    with pytest.raises(SystemExit) as e:
        main()
    assert e.value.code != 0
    _, err = capsys.readouterr()
    assert "usage: tuxrun" in err
