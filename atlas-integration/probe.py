"""Descobre o host da API do Atlas e o formato de autenticação.

Testa combinações de host x header em GET /queue (só leitura) e mostra
quais respondem JSON. Nunca imprime o token.

Uso: python3 probe.py   (lê ATLAS_TOKEN / ATLAS_BASE do ambiente ou de .env)
"""

import json
import os
import pathlib
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).parent

CANDIDATE_BASES = [
	"https://crm.atlascrmia.com.br",
	"https://crm.atlascrmia.com.br/api",
	"https://api.atlascrmia.com.br",
	"https://backend.atlascrmia.com.br",
	"https://apicrm.atlascrmia.com.br",
	"https://crmapi.atlascrmia.com.br",
]


def auth_styles(token):
	return {
		"Bearer": {"Authorization": f"Bearer {token}"},
		"Authorization (raw)": {"Authorization": token},
		"x-api-key": {"x-api-key": token},
		"token": {"token": token},
	}


def load_env():
	env_file = HERE / ".env"
	if env_file.exists():
		for line in env_file.read_text().splitlines():
			line = line.strip()
			if line and not line.startswith("#") and "=" in line:
				key, value = line.split("=", 1)
				os.environ.setdefault(key.strip(), value.strip())


def try_request(url, headers):
	req = urllib.request.Request(url, headers={"Accept": "application/json", **headers})
	try:
		with urllib.request.urlopen(req, timeout=10) as resp:
			return resp.status, resp.headers.get("Content-Type", ""), resp.read(300)
	except urllib.error.HTTPError as e:
		return e.code, e.headers.get("Content-Type", ""), e.read(300)
	except Exception as e:
		return None, "", str(e).encode()[:120]


def main():
	load_env()
	token = os.environ.get("ATLAS_TOKEN", "").strip()
	if not token:
		raise SystemExit("Defina ATLAS_TOKEN (no ambiente ou em .env).")

	base = os.environ.get("ATLAS_BASE", "").strip()
	bases = [base.rstrip("/")] if base else CANDIDATE_BASES

	for b in bases:
		for name, headers in auth_styles(token).items():
			status, ctype, body = try_request(f"{b}/queue", headers)
			is_json = "json" in ctype
			mark = "OK " if status == 200 and is_json else "   "
			snippet = body.decode(errors="replace").replace(token, "<TOKEN>").replace("\n", " ")
			print(f"{mark}{b:<40} {name:<20} {status} {ctype[:30]:<30} {snippet[:80]}")
			if status is None:
				break  # host inacessível; não adianta testar outros headers


if __name__ == "__main__":
	main()
