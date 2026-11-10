package com.fatec.veltis.dtos;

import java.util.List;

/**
 * Escola ou faculdade pronta para virar um pino no mapa do frontend.
 * Os nomes dos campos são os mesmos do mockData do site e da API Python.
 */
public record InstituicaoNoMapaResponse(
        String id,
        String origem,
        String tipo,
        String nome,
        String sigla,
        String nomeInstituicao,
        Long codigoInep,
        Long codigoIes,
        String municipio,
        String codigoMunicipio,
        String uf,
        String rede,
        String categoriaAdministrativa,
        String endereco,
        String bairro,
        String cep,
        String telefone,
        Double latitude,
        Double longitude,
        String precisaoLocalizacao,
        Integer anoCenso,
        String situacaoFuncionamento,
        Boolean possuiEnsinoMedio,
        String organizacaoAcademica,
        List<CursoNoMapaResponse> cursos) {
}
