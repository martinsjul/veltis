package com.fatec.veltis.exceptions;

/**
 * Lançada quando a operação fere uma regra do Veltis
 * (ex.: código duplicado, apagar município que ainda tem escolas). Vira HTTP 409.
 */
public class RegraDeNegocioException extends RuntimeException {

    public RegraDeNegocioException(String mensagem) {
        super(mensagem);
    }
}
