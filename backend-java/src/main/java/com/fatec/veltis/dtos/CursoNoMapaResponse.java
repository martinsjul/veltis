package com.fatec.veltis.dtos;

/** Curso dentro de um item do mapa (mesmo formato da API Python do Veltis). */
public record CursoNoMapaResponse(
        Long codigo,
        String nome,
        String grau,
        String area,
        Boolean gratuito,
        Integer vagas,
        Integer matriculas) {
}
