package com.fatec.veltis.dtos;

public record CursoSuperiorResponse(
        Long id,
        Long codigoEmec,
        String nome,
        String grau,
        String area,
        Boolean gratuito,
        Integer vagas,
        Integer matriculas,
        InstituicaoResumoResponse instituicao,
        MunicipioResumoResponse municipio) {
}
