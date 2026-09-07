from pathlib import Path

from truss.runtime import broker_binary, broker_password_binary


def test_finds_mosquitto_from_heroku_apt_directory(monkeypatch, tmp_path):
    broker = tmp_path / ".apt" / "usr" / "sbin" / "mosquitto"
    passwd = tmp_path / ".apt" / "usr" / "bin" / "mosquitto_passwd"
    broker.parent.mkdir(parents=True)
    passwd.parent.mkdir(parents=True)
    broker.touch()
    passwd.touch()
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("TRUSS_MOSQUITTO", raising=False)
    monkeypatch.setattr("truss.runtime.shutil.which", lambda _: None)

    assert broker_binary() == broker.resolve()
    assert broker_password_binary(broker) == passwd
