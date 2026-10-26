import hashlib
import pytest
from scripts.setup_lan_https import prepare_tls, openssl_path
from scripts.launch_web import make_environment, make_proxy_config


def test_https_configuration_is_scoped_to_selected_lan(tmp_path):
    tls = {"certificate":str(tmp_path/"server.pem"),"key":str(tmp_path/"server.key"),
           "ca":str(tmp_path/"LAN-LMS-CA.cer"),"origin":"https://192.168.1.100:8443"}
    source = "events {}\nhttp {\n server { listen 8080; location / { proxy_pass http://127.0.0.1:3000; } }\n}\n"
    config = make_proxy_config(source,"192.168.1.100",tls)
    assert "listen 192.168.1.100:8443 ssl;" in config
    assert "listen 127.0.0.1:8080;" in config
    assert "0.0.0.0" not in config
    assert config.count("proxy_pass http://127.0.0.1:3000") == 2
    assert "ssl_certificate_key" in config and "ssl_protocols TLSv1.2 TLSv1.3" in config
    env = make_environment(tmp_path,"192.168.1.100",tls)
    assert env["PUBLIC_ORIGIN"] == "http://192.168.1.100:8080"
    assert env["HTTPS_ORIGIN"] == tls["origin"]
    assert tls["origin"] in env["ALLOWED_ORIGINS"].split(",")
    assert env["LAN_CA_CERTIFICATE"] == tls["ca"]
    with pytest.raises(ValueError):
        make_proxy_config(source,None,tls)


def test_local_ca_and_certificate_are_reusable_without_installing_trust(tmp_path):
    try:
        openssl_path()
    except RuntimeError:
        pytest.skip("OpenSSL not installed")
    tls = prepare_tls(tmp_path,"192.168.1.100")
    key = (tmp_path/".runtime/tls/ca.key").read_bytes()
    second = prepare_tls(tmp_path,"192.168.1.100")
    assert tls == second
    assert (tmp_path/".runtime/tls/ca.key").read_bytes() == key
    assert hashlib.sha256((tmp_path/".runtime/tls/LAN-LMS-CA.cer").read_bytes()).hexdigest().upper() == tls["fingerprint"].replace(":","")
    moved = prepare_tls(tmp_path,"192.168.1.101")
    assert moved["fingerprint"] == tls["fingerprint"]
    assert moved["origin"] == "https://192.168.1.101:8443"
