# Local runtime packages

`packages/nginx-1.30.6.zip` contains the verified Windows Nginx 1.30.6 distribution already used by this project, with its upstream `docs/LICENSE` and other bundled notices. Logs/temp files are excluded. It is included so a GitHub source download can install the proxy without depending on nginx.org being reachable. The bootstrap checks the SHA-256 of `nginx.exe` before installing it.

Upstream: https://nginx.org/en/download.html

Extracted runtime files belong in `tools/nginx` (ignored by Git). Python/Node installed by the bootstrap live in `.runtime/bootstrap`; Docker/WSL are installed on the host through their official installers.
