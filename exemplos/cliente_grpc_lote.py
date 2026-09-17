import grpc

import inferencia_pb2
import inferencia_pb2_grpc


def main():
    canal = grpc.insecure_channel("localhost:50051")
    stub = inferencia_pb2_grpc.InferenciaStub(canal)

    pedido = inferencia_pb2.PedidoLote(
        textos=[
            "o atendimento foi otimo",
            "o produto chegou quebrado",
            "foi tudo normal"
        ]
    )

    resposta = stub.PreverLote(pedido)

    for resultado in resposta.resultados:
        print(
            resultado.texto,
            "->",
            resultado.sentimento,
            resultado.confianca
        )


if __name__ == "__main__":
    main()