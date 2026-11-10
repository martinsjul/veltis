package com.fatec.veltis.mappers;

import com.fatec.veltis.dtos.CursoSuperiorRequest;
import com.fatec.veltis.dtos.CursoSuperiorResponse;
import com.fatec.veltis.entities.CursoSuperior;

public final class CursoSuperiorMapper {

    private CursoSuperiorMapper() {
    }

    public static CursoSuperior toEntity(CursoSuperiorRequest dto) {
        CursoSuperior c = new CursoSuperior();
        copiar(dto, c);
        return c;
    }

    public static void copiar(CursoSuperiorRequest dto, CursoSuperior c) {
        c.setCodigoEmec(dto.codigoEmec());
        c.setNome(dto.nome().trim());
        c.setGrau(dto.grau());
        c.setArea(dto.area());
        c.setGratuito(dto.gratuito());
        c.setVagas(dto.vagas());
        c.setMatriculas(dto.matriculas());
    }

    public static CursoSuperiorResponse toResponse(CursoSuperior c) {
        return new CursoSuperiorResponse(
                c.getId(),
                c.getCodigoEmec(),
                c.getNome(),
                c.getGrau() == null ? null : c.getGrau().name(),
                c.getArea(),
                c.getGratuito(),
                c.getVagas(),
                c.getMatriculas(),
                InstituicaoMapper.toResumo(c.getInstituicao()),
                MunicipioMapper.toResumo(c.getMunicipio()));
    }
}
