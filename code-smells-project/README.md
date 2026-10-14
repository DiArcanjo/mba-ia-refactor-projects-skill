# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000`. Host, porta, debug e demais opções vêm de variáveis de ambiente (veja `.env.example`); o `/admin/reset-db` exige `Authorization: Bearer <token>` de um admin (token retornado pelo `/login`). O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo.
