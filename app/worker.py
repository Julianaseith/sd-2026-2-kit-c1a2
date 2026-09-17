"""
Worker: consome a fila e executa a inferencia.

O QUE JA ESTA PRONTO: o laco principal e o carregamento do modelo.
O QUE VOCE PRECISA FAZER (TAREFAS.md, itens 3 e 5):
  - guardar o resultado ao terminar
  - tratar erro com retentativa e fila de descarte (dead-letter)

Rodar:  python -m app.worker
Suba mais de um worker em terminais diferentes e veja a carga se dividir.
"""
import json
import logging
import time


from app import fila
from app.modelo import carregar_modelo


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)




def main():
    print("[worker] carregando modelo...")
    modelo = carregar_modelo()
    print("[worker] pronto. aguardando tarefas (Ctrl+C para sair)")

    while True:
        tarefa = fila.proxima_tarefa(timeout=5)
        if tarefa is None:
            continue

        print(f"[worker] processando {tarefa['id']}")
        inicio = time.time()

        try:
            resultado = modelo.prever(tarefa["texto"])
            resultado["status"] = "pronto"
            resultado["tempo_ms"] = round((time.time() - inicio) * 1000, 2)

            fila.guardar_resultado(tarefa["id"], resultado)

            logger.info(
                "WORKER | id=%s | tamanho=%d | tempo_ms=%.2f",
                tarefa["id"],
                len(tarefa["texto"]),
                resultado["tempo_ms"]
            )

        except Exception as erro:
            tentativas = tarefa.get("tentativas", 0) + 1

            print(
                f"[worker] ERRO em {tarefa['id']}: {erro} "
                f"(tentativa {tentativas}/3)"
            )

            if tentativas < 3:
                tarefa["tentativas"] = tentativas

                fila.cliente().rpush(
                    fila.FILA_TAREFAS,
                    json.dumps(tarefa)
                )

                print(
                    f"[worker] tarefa {tarefa['id']} devolvida para a fila"
                )

            else:
                fila.cliente().rpush(
                    "dead-letter",
                    json.dumps(tarefa)
                )

                fila.guardar_resultado(
                    tarefa["id"],
                    {
                        "status": "erro",
                        "erro": str(erro),
                        "tentativas": tentativas
                    }
                )

                print(
                    f"[worker] tarefa {tarefa['id']} enviada para dead-letter"
                )


if __name__ == "__main__":
    main()
