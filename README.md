# Serviço de Inferência Distribuído - C1.A2

Trabalho da disciplina de Sistemas Distribuídos e Computação em Nuvem.

O projeto implementa um serviço de inferência de sentimento utilizando duas interfaces de comunicação:

- REST com FastAPI
- gRPC com Protocol Buffers

O processamento pela interface REST é assíncrono, utilizando Redis como fila e um worker responsável pela execução da inferência.

---

## Arquitetura

Fluxo da interface REST:

Cliente → FastAPI → Redis → Worker → Modelo → Redis → Cliente

1. O cliente envia um texto para `POST /predict`.
2. A API coloca a tarefa na fila Redis.
3. A API devolve imediatamente um identificador da tarefa.
4. O worker retira a tarefa da fila.
5. O modelo executa a inferência.
6. O worker salva o resultado.
7. O cliente consulta o resultado em `GET /resultado/{id}`.

O projeto também possui uma interface gRPC com os métodos:

- `Prever`: processa um texto.
- `PreverLote`: processa vários textos em uma mesma chamada.

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
app/
├── api_rest.py
├── fila.py
├── modelo.py
├── servidor_grpc.py
└── worker.py

proto/
└── inferencia.proto

exemplos/
├── cliente_rest.py
└── cliente_grpc_lote.py