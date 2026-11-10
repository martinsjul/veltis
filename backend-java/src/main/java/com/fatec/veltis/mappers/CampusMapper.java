package com.fatec.veltis.mappers;

import com.fatec.veltis.dtos.CampusRequest;
import com.fatec.veltis.dtos.CampusResponse;
import com.fatec.veltis.entities.Campus;

public final class CampusMapper {

    private CampusMapper() {
    }

    /** Instituição e município são associados pelo service. */
    public static Campus toEntity(CampusRequest dto) {
        Campus c = new Campus();
        copiar(dto, c);
        return c;
    }

    public static void copiar(CampusRequest dto, Campus c) {
        c.setNome(dto.nome().trim());
        c.setEndereco(dto.endereco());
        c.setBairro(dto.bairro());
        c.setCep(dto.cep());
        c.setLatitude(dto.latitude());
        c.setLongitude(dto.longitude());
        c.setPrecisao(dto.precisao());
    }

    public static CampusResponse toResponse(Campus c) {
        return new CampusResponse(
                c.getId(),
                c.getNome(),
                c.getEndereco(),
                c.getBairro(),
                c.getCep(),
                c.getLatitude(),
                c.getLongitude(),
                c.getPrecisao().name(),
                InstituicaoMapper.toResumo(c.getInstituicao()),
                MunicipioMapper.toResumo(c.getMunicipio()));
    }
}
