# Atlas CRM — integração

Pasta isolada do resto do repositório para a integração com a API do Atlas CRM.

## Setup

```bash
cd atlas-integration
cp .env.example .env   # preencha ATLAS_TOKEN
python3 probe.py       # descobre host da API + formato do header
```

O `.env` está no `.gitignore` — o token nunca vai para o git.
