package com.fatec.veltis.mappers;

import com.fatec.veltis.dtos.MunicipioRequest;
import com.fatec.veltis.dtos.MunicipioResponse;
import com.fatec.veltis.dtos.MunicipioResumoResponse;
import com.fatec.veltis.entities.Municipio;

/** Converte Municipio (entidade) <-> DTOs. Só copia campos; regras ficam no service. */
public final class MunicipioMapper {

    private MunicipioMapper() {
    }

    public static Municipio toEntity(MunicipioRequest dto) {
        Municipio m = new Municipio();
        m.setCodigo(dto.codigo());
        copiar(dto, m);
        return m;
    }

    /** Usado no PUT: atualiza a entidade que já existe (o código não muda). */
    public static void copiar(MunicipioRequest dto, Municipio m) {
        m.setNome(dto.nome().trim());
        m.setPopulacao2022(dto.populacao2022());
        m.setAreaKm2(dto.areaKm2());
    }

    public static MunicipioResponse toResponse(Municipio m) {
        return new MunicipioResponse(m.getCodigo(), m.getNome(), m.getPopulacao2022(), m.getAreaKm2());
    }

    public static MunicipioResumoResponse toResumo(Municipio m) {
        return new MunicipioResumoResponse(m.getCodigo(), m.getNome());
    }
}
