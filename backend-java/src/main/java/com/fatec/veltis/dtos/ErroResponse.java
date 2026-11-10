package com.fatec.veltis.dtos;

import java.time.LocalDateTime;
import java.util.List;

/**
 * Corpo padrão de erro da API.
 * Ex.: { "status": 404, "erro": "Não encontrado", "mensagem": "Escola 123 não encontrada.", ... }
 */
public record ErroResponse(
        LocalDateTime dataHora,
        int status,
        String erro,
        String mensagem,
        String caminho,
        List<CampoInvalido> campos) {

    /** Um campo do JSON (ou parâmetro) que não passou na validação. */
    public record CampoInvalido(String campo, String mensagem) {
    }
}
