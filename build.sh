#!/usr/bin/env bash
# Sai do script se qualquer comando der erro
set -o errexit

# 1. Instala as dependências
pip install -r requirements.txt

# 2. Coleta os arquivos estáticos
python manage.py collectstatic --noinput

# 3. Aplica as migrações no banco de dados
python manage.py migrate
