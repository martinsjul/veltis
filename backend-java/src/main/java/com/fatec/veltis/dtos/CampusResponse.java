package com.fatec.veltis.dtos;

public record CampusResponse(
        Long id,
        String nome,
        String endereco,
        String bairro,
        String cep,
        Double latitude,
        Double longitude,
        String precisao,
        InstituicaoResumoResponse instituicao,
        MunicipioResumoResponse municipio) {
}
