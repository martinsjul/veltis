package com.fatec.veltis.exceptions;

/** Pedido mal formado que a Bean Validation não pega sozinha. Vira HTTP 400. */
public class RequisicaoInvalidaException extends RuntimeException {

    public RequisicaoInvalidaException(String mensagem) {
        super(mensagem);
    }
}
