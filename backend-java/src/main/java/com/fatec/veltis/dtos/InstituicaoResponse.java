package com.fatec.veltis.dtos;

public record InstituicaoResponse(
        Long codigoIes,
        String nome,
        String sigla,
        String tipo,
        String rede,
        String organizacaoAcademica,
        int quantidadeCampi,
        int quantidadeCursos) {
}
