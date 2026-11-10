package com.fatec.veltis.mappers;

import java.util.Comparator;
import java.util.List;

import com.fatec.veltis.dtos.CursoTecnicoResponse;
import com.fatec.veltis.dtos.EscolaDetalheResponse;
import com.fatec.veltis.dtos.EscolaRequest;
import com.fatec.veltis.dtos.EscolaResumoResponse;
import com.fatec.veltis.dtos.LocalizacaoRequest;
import com.fatec.veltis.dtos.LocalizacaoResponse;
import com.fatec.veltis.entities.Escola;
import com.fatec.veltis.entities.LocalizacaoEscola;

/**
 * Converte Escola <-> DTOs.
 *
 * Os relacionamentos viram DTOs pequenos (MunicipioResumoResponse, CursoTecnicoResponse).
 * Assim o JSON nunca entra em ciclo (escola -> município -> escolas -> município...).
 */
public final class EscolaMapper {

    private EscolaMapper() {
    }

    /** O município não vem aqui: o service busca pelo código e associa. */
    public static Escola toEntity(EscolaRequest dto) {
        Escola e = new Escola();
        e.setCodigoInep(dto.codigoInep());
        copiar(dto, e);
        return e;
    }

    public static void copiar(EscolaRequest dto, Escola e) {
        e.setNome(dto.nome().trim());
        e.setDependencia(dto.dependencia());
        e.setSituacao(dto.situacao());
        e.setEndereco(dto.endereco());
        e.setCep(dto.cep());
        e.setTelefone(dto.telefone());
        e.setOfereceEnsinoMedio(Boolean.TRUE.equals(dto.ofereceEnsinoMedio()));
    }

    public static String tipo(Escola e) {
        return e.isEtec() ? "ETEC" : "Escola";
    }

    public static EscolaResumoResponse toResumo(Escola e) {
        return new EscolaResumoResponse(
                e.getCodigoInep(),
                e.getNome(),
                tipo(e),
                e.getDependencia().name(),
                e.getSituacao().name(),
                MunicipioMapper.toResumo(e.getMunicipio()),
                e.getLocalizacao() != null);
    }

    public static EscolaDetalheResponse toDetalhe(Escola e) {
        List<CursoTecnicoResponse> cursos = e.getCursosTecnicos().stream()
                .sorted(Comparator.comparing(c -> c.getNome()))
                .map(CursoTecnicoMapper::toResponse)
                .toList();

        return new EscolaDetalheResponse(
                e.getCodigoInep(),
                e.getNome(),
                tipo(e),
                e.getDependencia().name(),
                e.getSituacao().name(),
                e.getEndereco(),
                e.getCep(),
                e.getTelefone(),
                e.isOfereceEnsinoMedio(),
                MunicipioMapper.toResumo(e.getMunicipio()),
                toResponse(e.getLocalizacao()),
                cursos);
    }

    public static LocalizacaoEscola toEntity(LocalizacaoRequest dto) {
        return new LocalizacaoEscola(dto.latitude(), dto.longitude(), dto.fonte().trim(), dto.precisao());
    }

    public static LocalizacaoResponse toResponse(LocalizacaoEscola l) {
        if (l == null) {
            return null;
        }
        return new LocalizacaoResponse(l.getLatitude(), l.getLongitude(), l.getFonte(), l.getPrecisao());
    }
}
