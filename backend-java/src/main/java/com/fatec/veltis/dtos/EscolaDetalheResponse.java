package com.fatec.veltis.dtos;

import java.util.List;

/**
 * Ficha completa da escola, com os relacionamentos já convertidos em DTOs:
 * município (N:1), localização (1:1) e cursos técnicos (N:N).
 */
public record EscolaDetalheResponse(
        Long codigoInep,
        String nome,
        String tipo,
        String dependencia,
        String situacao,
        String endereco,
        String cep,
        String telefone,
        boolean ofereceEnsinoMedio,
        MunicipioResumoResponse municipio,
        LocalizacaoResponse localizacao,
        List<CursoTecnicoResponse> cursosTecnicos) {
}
