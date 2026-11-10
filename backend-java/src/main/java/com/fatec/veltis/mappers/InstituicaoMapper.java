package com.fatec.veltis.mappers;

import com.fatec.veltis.dtos.InstituicaoRequest;
import com.fatec.veltis.dtos.InstituicaoResponse;
import com.fatec.veltis.dtos.InstituicaoResumoResponse;
import com.fatec.veltis.entities.InstituicaoEnsinoSuperior;

public final class InstituicaoMapper {

    private InstituicaoMapper() {
    }

    public static InstituicaoEnsinoSuperior toEntity(InstituicaoRequest dto) {
        InstituicaoEnsinoSuperior i = new InstituicaoEnsinoSuperior();
        i.setCodigoIes(dto.codigoIes());
        copiar(dto, i);
        return i;
    }

    public static void copiar(InstituicaoRequest dto, InstituicaoEnsinoSuperior i) {
        i.setNome(dto.nome().trim());
        i.setSigla(dto.sigla());
        i.setRede(dto.rede());
        i.setOrganizacaoAcademica(dto.organizacaoAcademica());
    }

    public static String tipo(InstituicaoEnsinoSuperior i) {
        return i.isFatec() ? "FATEC" : "Faculdade/Universidade";
    }

    public static InstituicaoResponse toResponse(InstituicaoEnsinoSuperior i) {
        return new InstituicaoResponse(
                i.getCodigoIes(),
                i.getNome(),
                i.getSigla(),
                tipo(i),
                i.getRede().name(),
                i.getOrganizacaoAcademica(),
                i.getCampi().size(),
                i.getCursos().size());
    }

    public static InstituicaoResumoResponse toResumo(InstituicaoEnsinoSuperior i) {
        return new InstituicaoResumoResponse(i.getCodigoIes(), i.getNome(), i.getSigla());
    }
}
