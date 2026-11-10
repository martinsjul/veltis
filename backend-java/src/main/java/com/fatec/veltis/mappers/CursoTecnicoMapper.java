package com.fatec.veltis.mappers;

import com.fatec.veltis.dtos.CursoTecnicoRequest;
import com.fatec.veltis.dtos.CursoTecnicoResponse;
import com.fatec.veltis.entities.CursoTecnico;

public final class CursoTecnicoMapper {

    private CursoTecnicoMapper() {
    }

    public static CursoTecnico toEntity(CursoTecnicoRequest dto) {
        CursoTecnico c = new CursoTecnico();
        c.setCodigo(dto.codigo());
        copiar(dto, c);
        return c;
    }

    public static void copiar(CursoTecnicoRequest dto, CursoTecnico c) {
        c.setNome(dto.nome().trim());
        c.setArea(dto.area());
    }

    public static CursoTecnicoResponse toResponse(CursoTecnico c) {
        return new CursoTecnicoResponse(c.getCodigo(), c.getNome(), c.getArea());
    }
}
