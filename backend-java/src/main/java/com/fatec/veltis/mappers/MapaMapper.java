package com.fatec.veltis.mappers;

import java.util.Comparator;
import java.util.List;

import com.fatec.veltis.dtos.CursoNoMapaResponse;
import com.fatec.veltis.dtos.InstituicaoNoMapaResponse;
import com.fatec.veltis.entities.Campus;
import com.fatec.veltis.entities.CursoSuperior;
import com.fatec.veltis.entities.Escola;

/**
 * Monta o item do mapa a partir de uma Escola ou de um Campus.
 * O formato é igual ao do endpoint /mapa/instituicoes da API Python,
 * para o frontend funcionar com qualquer um dos dois backends.
 */
public final class MapaMapper {

    /** Edições usadas nos dados de demonstração. */
    public static final int ANO_CENSO_ESCOLAR = 2025;
    public static final int ANO_CENSO_SUPERIOR = 2024;

    private MapaMapper() {
    }

    public static InstituicaoNoMapaResponse daEscola(Escola e) {
        List<CursoNoMapaResponse> cursos = e.getCursosTecnicos().stream()
                .sorted(Comparator.comparing(c -> c.getNome()))
                .map(c -> new CursoNoMapaResponse(c.getCodigo(), c.getNome(), null, c.getArea(), null, null, null))
                .toList();

        return new InstituicaoNoMapaResponse(
                "escola-" + e.getCodigoInep(),
                "INEP_ESCOLA",
                EscolaMapper.tipo(e),
                e.getNome(),
                null,
                null,
                e.getCodigoInep(),
                null,
                e.getMunicipio().getNome(),
                e.getMunicipio().getCodigo(),
                "SP",
                e.getDependencia().getRotulo(),
                null,
                e.getEndereco(),
                null,
                formatarCep(e.getCep()),
                e.getTelefone(),
                e.getLocalizacao().getLatitude(),
                e.getLocalizacao().getLongitude(),
                e.getLocalizacao().getPrecisao(),
                ANO_CENSO_ESCOLAR,
                e.getSituacao().getRotulo(),
                e.isOfereceEnsinoMedio(),
                null,
                cursos);
    }

    /** cursosNoMunicipio = cursos da instituição oferecidos no município do campus (RN-09). */
    public static InstituicaoNoMapaResponse doCampus(Campus c, List<CursoSuperior> cursosNoMunicipio) {
        List<CursoNoMapaResponse> cursos = cursosNoMunicipio.stream()
                .sorted(Comparator.comparing(CursoSuperior::getNome))
                .map(cs -> new CursoNoMapaResponse(
                        cs.getCodigoEmec(),
                        cs.getNome(),
                        cs.getGrau() == null ? null : cs.getGrau().getRotulo(),
                        cs.getArea(),
                        cs.getGratuito(),
                        cs.getVagas(),
                        cs.getMatriculas()))
                .toList();

        return new InstituicaoNoMapaResponse(
                "ies-" + c.getInstituicao().getCodigoIes() + "-" + c.getId(),
                "MEC_IES",
                InstituicaoMapper.tipo(c.getInstituicao()),
                c.getNome(),
                c.getInstituicao().getSigla(),
                c.getInstituicao().getNome(),
                null,
                c.getInstituicao().getCodigoIes(),
                c.getMunicipio().getNome(),
                c.getMunicipio().getCodigo(),
                "SP",
                c.getInstituicao().getRede().getRotulo(),
                null,
                c.getEndereco(),
                c.getBairro(),
                formatarCep(c.getCep()),
                null,
                c.getLatitude(),
                c.getLongitude(),
                c.getPrecisao().getValor(),
                ANO_CENSO_SUPERIOR,
                "Em atividade",
                false,
                c.getInstituicao().getOrganizacaoAcademica(),
                cursos);
    }

    /** "18013280" -> "18013-280". */
    static String formatarCep(String cep) {
        if (cep == null || cep.length() != 8) {
            return null;
        }
        return cep.substring(0, 5) + "-" + cep.substring(5);
    }
}
