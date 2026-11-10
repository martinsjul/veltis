package com.fatec.veltis.services;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.fatec.veltis.dtos.InstituicaoNoMapaResponse;
import com.fatec.veltis.entities.Campus;
import com.fatec.veltis.entities.CursoSuperior;
import com.fatec.veltis.entities.Escola;
import com.fatec.veltis.mappers.MapaMapper;
import com.fatec.veltis.repositories.CampusRepository;
import com.fatec.veltis.repositories.CursoSuperiorRepository;
import com.fatec.veltis.repositories.EscolaRepository;

/**
 * Lista única de escolas e faculdades com latitude e longitude, para os pinos do mapa.
 * É o endpoint que o frontend do Veltis usa.
 */
@Service
public class MapaService {

    /** Tipos de pino aceitos no filtro ?tipo= */
    public enum TipoNoMapa { ESCOLA, ETEC, FATEC, FACULDADE }

    private final EscolaRepository escolaRepository;
    private final CampusRepository campusRepository;
    private final CursoSuperiorRepository cursoSuperiorRepository;

    public MapaService(EscolaRepository escolaRepository, CampusRepository campusRepository,
                       CursoSuperiorRepository cursoSuperiorRepository) {
        this.escolaRepository = escolaRepository;
        this.campusRepository = campusRepository;
        this.cursoSuperiorRepository = cursoSuperiorRepository;
    }

    @Transactional(readOnly = true)
    public List<InstituicaoNoMapaResponse> instituicoes(String municipio, List<TipoNoMapa> tiposPedidos,
                                                        boolean apenasAtivas) {
        Set<TipoNoMapa> tipos = (tiposPedidos == null || tiposPedidos.isEmpty())
                ? EnumSet.allOf(TipoNoMapa.class)
                : EnumSet.copyOf(tiposPedidos);

        List<InstituicaoNoMapaResponse> resultado = new ArrayList<>();

        if (tipos.contains(TipoNoMapa.ESCOLA) || tipos.contains(TipoNoMapa.ETEC)) {
            for (Escola e : escolaRepository.buscarComLocalizacao(municipio)) {
                boolean querEsteTipo = e.isEtec() ? tipos.contains(TipoNoMapa.ETEC) : tipos.contains(TipoNoMapa.ESCOLA);
                if (querEsteTipo && (!apenasAtivas || e.isEmAtividade())) {
                    resultado.add(MapaMapper.daEscola(e));
                }
            }
        }

        if (tipos.contains(TipoNoMapa.FATEC) || tipos.contains(TipoNoMapa.FACULDADE)) {
            // Cursos agrupados por "instituição|município" para achar os cursos de cada campus (RN-09).
            Map<String, List<CursoSuperior>> cursosPorLocal = cursoSuperiorRepository.buscar(municipio, null).stream()
                    .collect(Collectors.groupingBy(c -> chave(c.getInstituicao().getCodigoIes(), c.getMunicipio().getCodigo())));

            for (Campus c : campusRepository.buscar(municipio, null)) {
                boolean fatec = c.getInstituicao().isFatec();
                if (fatec ? tipos.contains(TipoNoMapa.FATEC) : tipos.contains(TipoNoMapa.FACULDADE)) {
                    List<CursoSuperior> cursos = cursosPorLocal.getOrDefault(
                            chave(c.getInstituicao().getCodigoIes(), c.getMunicipio().getCodigo()), List.of());
                    resultado.add(MapaMapper.doCampus(c, cursos));
                }
            }
        }

        resultado.sort(Comparator.comparing(InstituicaoNoMapaResponse::municipio)
                .thenComparing(InstituicaoNoMapaResponse::nome));
        return resultado;
    }

    private static String chave(Long instituicao, String municipio) {
        return instituicao + "|" + municipio;
    }
}
