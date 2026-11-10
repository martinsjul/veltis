package com.fatec.veltis.dtos;

/** Escola na listagem (poucos campos, para a lista ficar leve). */
public record EscolaResumoResponse(
        Long codigoInep,
        String nome,
        String tipo,
        String dependencia,
        String situacao,
        MunicipioResumoResponse municipio,
        boolean temLocalizacao) {
}
