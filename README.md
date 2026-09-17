# Serviço de Inferência Distribuído - C1.A2

Trabalho da disciplina de **Sistemas Distribuídos e Computação em Nuvem**.

O projeto implementa um serviço de inferência de sentimento utilizando duas interfaces de comunicação:

- REST com FastAPI
- gRPC com Protocol Buffers

A interface REST utiliza processamento assíncrono com Redis e um worker. O cliente envia o texto, recebe um identificador da tarefa e pode consultar o resultado posteriormente.

As interfaces REST e gRPC utilizam o mesmo modelo de inferência.

---

## Arquitetura

### Interface REST assíncrona

Fluxo:

```text
Cliente
   ↓
FastAPI
   ↓
Redis - fila de tarefas
   ↓
Worker
   ↓
Modelo de inferência
   ↓
Redis - resultado
   ↓
Cliente consulta o resultado
```

Funcionamento:

1. O cliente envia um texto para `POST /predict`.
2. A API coloca a tarefa na fila Redis.
3. A API devolve imediatamente um identificador da tarefa com HTTP 202.
4. O worker retira a tarefa da fila.
5. O modelo executa a inferência.
6. O worker salva o resultado no Redis.
7. O cliente consulta o resultado usando `GET /resultado/{id}`.

### Interface gRPC

O serviço gRPC possui dois métodos:

- `Prever`: recebe um texto e devolve uma previsão.
- `PreverLote`: recebe vários textos e devolve várias previsões em uma única chamada.

---

## Tecnologias utilizadas

- Python 3.12
- FastAPI
- Uvicorn
- gRPC
- Protocol Buffers
- Redis
- Docker
- scikit-learn

---

## Estrutura do projeto

```text
sd-2026-2-kit-c1a2/
├── app/
│   ├── api_rest.py
│   ├── fila.py
│   ├── modelo.py
│   ├── servidor_grpc.py
│   └── worker.py
├── exemplos/
│   ├── cliente_rest.py
│   └── cliente_grpc_lote.py
├── proto/
│   └── inferencia.proto
├── scripts/
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

# Como executar

## 1. Clonar o repositório

```powershell
git clone https://github.com/Julianaseith/sd-2026-2-kit-c1a2.git
cd sd-2026-2-kit-c1a2
```

---

## 2. Criar o ambiente virtual

Este projeto foi testado utilizando **Python 3.12**.

No Windows:

```powershell
py -3.12 -m venv .venv
```

Ative o ambiente:

```powershell
.venv\Scripts\activate
```

Para confirmar a versão:

```powershell
python --version
```

O esperado é algo semelhante a:

```text
Python 3.12.x
```

---

## 3. Instalar as dependências

Com o ambiente virtual ativado:

```powershell
python -m pip install -r requirements.txt
```

---

## 4. Subir o Redis

É necessário ter o Docker Desktop instalado e em execução.

Execute:

```powershell
docker compose up -d
```

Para verificar:

```powershell
docker ps
```

O container do Redis deve aparecer em execução.

---

# Interface REST

## 5. Rodar a API REST

Em um terminal com o ambiente virtual ativado:

```powershell
uvicorn app.api_rest:app --reload --port 8000
```

A documentação automática do FastAPI ficará disponível em:

```text
http://localhost:8000/docs
```

---

## 6. Rodar o worker

Abra outro terminal na pasta do projeto.

Ative o ambiente:

```powershell
.venv\Scripts\activate
```

Depois execute:

```powershell
python -m app.worker
```

O worker ficará aguardando tarefas da fila Redis.

---

## Testando POST /predict

Abra:

```text
http://localhost:8000/docs
```

Utilize:

```text
POST /predict
```

Exemplo de entrada:

```json
{
  "texto": "o atendimento foi otimo"
}
```

A API deve responder com código HTTP `202` e um identificador:

```json
{
  "id": "identificador-da-tarefa"
}
```

A inferência não é executada diretamente nessa requisição. A tarefa é colocada na fila para ser processada pelo worker.

---

## Testando GET /resultado/{id}

Copie o identificador retornado pelo `POST /predict`.

Utilize:

```text
GET /resultado/{tarefa_id}
```

Enquanto a tarefa ainda não tiver sido processada, a resposta pode ser:

```json
{
  "status": "na_fila"
}
```

Depois que o worker processar a tarefa, será retornado algo semelhante a:

```json
{
  "texto": "o atendimento foi otimo",
  "sentimento": "positivo",
  "confianca": 0.5469,
  "status": "pronto",
  "tempo_ms": 0.95
}
```

---

# Interface gRPC

## 7. Gerar os stubs

Na raiz do projeto:

```powershell
python -m grpc_tools.protoc -I proto --python_out=. --grpc_python_out=. proto/inferencia.proto
```

Esse comando gera os arquivos:

```text
inferencia_pb2.py
inferencia_pb2_grpc.py
```

---

## 8. Rodar o servidor gRPC

Em um terminal com o ambiente virtual ativado:

```powershell
python -m app.servidor_grpc
```

O esperado é:

```text
[grpc] carregando modelo...
[grpc] modelo pronto
[grpc] escutando na porta 50051
```

---

## 9. Testar PreverLote

Com o servidor gRPC rodando, abra outro terminal e execute:

```powershell
python -m exemplos.cliente_grpc_lote
```

O cliente envia vários textos em uma única chamada.

Exemplo de saída:

```text
o atendimento foi otimo -> positivo 0.5469
o produto chegou quebrado -> positivo 0.5531
foi tudo normal -> positivo 0.5524
```

O objetivo desse teste é demonstrar que o método `PreverLote` recebe vários textos e devolve vários resultados.

A qualidade da classificação depende do modelo utilizado.

---

# Tratamento de falhas

O worker possui mecanismo de retentativa.

Quando ocorre um erro durante a inferência:

```text
1ª falha → tarefa volta para a fila
2ª falha → tarefa volta para a fila
3ª falha → tarefa vai para dead-letter
```

Após três tentativas sem sucesso, a tarefa é enviada para a fila:

```text
dead-letter
```

O resultado associado ao identificador da tarefa também passa a registrar o erro.

Exemplo:

```json
{
  "status": "erro",
  "erro": "descricao do erro",
  "tentativas": 3
}
```

Isso evita que uma tarefa com erro permaneça sendo processada indefinidamente.

---

# Logs

Os principais serviços registram informações sobre as requisições e tarefas processadas.

São registrados:

- identificador;
- tamanho da entrada;
- tempo de processamento.

Exemplo REST:

```text
POST /predict | id=... | tamanho=23 | tempo_ms=1.42
```

Exemplo worker:

```text
WORKER | id=... | tamanho=23 | tempo_ms=0.95
```

Exemplo gRPC:

```text
gRPC PreverLote | id=... | tamanho=65 | tempo_ms=1.20
```

Os logs são exibidos nos respectivos terminais durante a execução.

---

# Encerrando o Redis

Quando terminar os testes, os containers podem ser encerrados com:

```powershell
docker compose down
```

---

# Teste de instalação do zero

Antes da entrega, recomenda-se testar o projeto como se fosse um novo usuário:

```powershell
git clone https://github.com/Julianaseith/sd-2026-2-kit-c1a2.git teste-entrega-c1a2

cd teste-entrega-c1a2

py -3.12 -m venv .venv

.venv\Scripts\activate

python -m pip install -r requirements.txt

docker compose up -d
```

Depois devem ser testados:

```powershell
uvicorn app.api_rest:app --reload --port 8000
```

Em outro terminal:

```powershell
python -m app.worker
```

Para o gRPC:

```powershell
python -m grpc_tools.protoc -I proto --python_out=. --grpc_python_out=. proto/inferencia.proto

python -m app.servidor_grpc
```

E, em outro terminal:

```powershell
python -m exemplos.cliente_grpc_lote
```

Se REST, worker, Redis e gRPC funcionarem seguindo apenas estas instruções, o projeto está pronto para entrega.