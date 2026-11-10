package com.fatec.veltis.services;

import java.util.List;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.fatec.veltis.dtos.CursoTecnicoResponse;
import com.fatec.veltis.dtos.EscolaDetalheResponse;
import com.fatec.veltis.dtos.EscolaRequest;
import com.fatec.veltis.dtos.EscolaResumoResponse;
import com.fatec.veltis.dtos.LocalizacaoRequest;
import com.fatec.veltis.dtos.LocalizacaoResponse;
import com.fatec.veltis.entities.CursoTecnico;
import com.fatec.veltis.entities.Escola;
import com.fatec.veltis.entities.LocalizacaoEscola;
import com.fatec.veltis.enums.Dependencia;
import com.fatec.veltis.exceptions.RecursoNaoEncontradoException;
import com.fatec.veltis.exceptions.RegraDeNegocioException;
import com.fatec.veltis.exceptions.RequisicaoInvalidaException;
import com.fatec.veltis.mappers.CursoTecnicoMapper;
import com.fatec.veltis.mappers.EscolaMapper;
import com.fatec.veltis.repositories.EscolaRepository;

/** Regras de negócio das escolas, da localização (1:1) e dos cursos técnicos (N:N). */
@Service
public class EscolaService {

    private final EscolaRepository escolaRepository;
    private final MunicipioService municipioService;
    private final CursoTecnicoService cursoTecnicoService;

    public EscolaService(EscolaRepository escolaRepository, MunicipioService municipioService,
                         CursoTecnicoService cursoTecnicoService) {
        this.escolaRepository = escolaRepository;
        this.municipioService = municipioService;
        this.cursoTecnicoService = cursoTecnicoService;
    }

    // ------------------------------------------------------------ CRUD

    @Transactional(readOnly = true)
    public Page<EscolaResumoResponse> listar(String municipio, Dependencia dependencia, String nome, Pageable pageable) {
        String trecho = (nome == null || nome.isBlank()) ? null : nome.trim();
        return escolaRepository.buscar(municipio, dependencia, trecho, pageable).map(EscolaMapper::toResumo);
    }

    @Transactional(readOnly = true)
    public EscolaDetalheResponse buscar(Long codigoInep) {
        return EscolaMapper.toDetalhe(obterComDetalhes(codigoInep));
    }

    @Transactional
    public EscolaDetalheResponse criar(EscolaRequest dto) {
        if (escolaRepository.existsById(dto.codigoInep())) {
            throw new RegraDeNegocioException("Já existe uma escola com o código INEP " + dto.codigoInep() + ".");
        }
        Escola escola = EscolaMapper.toEntity(dto);
        // Associação N:1: busca o município pelo código e liga na escola (preenche a FK municipio_codigo).
        escola.setMunicipio(municipioService.obter(dto.municipioCodigo()));
        return EscolaMapper.toDetalhe(escolaRepository.save(escola));
    }

    @Transactional
    public EscolaDetalheResponse atualizar(Long codigoInep, EscolaRequest dto) {
        if (!codigoInep.equals(dto.codigoInep())) {
            throw new RequisicaoInvalidaException("O código INEP do corpo (" + dto.codigoInep()
                    + ") deve ser igual ao da URL (" + codigoInep + ").");
        }
        Escola escola = obterComDetalhes(codigoInep);
        EscolaMapper.copiar(dto, escola);
        escola.setMunicipio(municipioService.obter(dto.municipioCodigo()));
        return EscolaMapper.toDetalhe(escola);
    }

    /**
     * Apaga a escola. A localização vai junto (cascade + orphanRemoval no 1:1) e as
     * linhas da tabela de junção escola_curso_tecnico são removidas pelo Hibernate,
     * porque a Escola é a dona do N:N. Os cursos técnicos continuam existindo.
     */
    @Transactional
    public void excluir(Long codigoInep) {
        Escola escola = obterComDetalhes(codigoInep);
        for (CursoTecnico curso : List.copyOf(escola.getCursosTecnicos())) {
            escola.removerCursoTecnico(curso);
        }
        escolaRepository.delete(escola);
    }

    // ------------------------------------------------------------ 1:1 localização

    /** Cria ou troca o ponto da escola no mapa. */
    @Transactional
    public LocalizacaoResponse definirLocalizacao(Long codigoInep, LocalizacaoRequest dto) {
        Escola escola = obterComDetalhes(codigoInep);
        LocalizacaoEscola atual = escola.getLocalizacao();
        if (atual == null) {
            escola.definirLocalizacao(EscolaMapper.toEntity(dto));
        } else {
            atual.setLatitude(dto.latitude());
            atual.setLongitude(dto.longitude());
            atual.setFonte(dto.fonte().trim());
            atual.setPrecisao(dto.precisao());
        }
        escolaRepository.saveAndFlush(escola);
        return EscolaMapper.toResponse(escola.getLocalizacao());
    }

    @Transactional
    public void removerLocalizacao(Long codigoInep) {
        Escola escola = obterComDetalhes(codigoInep);
        if (escola.getLocalizacao() == null) {
            throw new RecursoNaoEncontradoException("A escola " + codigoInep + " não tem localização cadastrada.");
        }
        escola.definirLocalizacao(null); // orphanRemoval apaga a linha da localização
    }

    // ------------------------------------------------------------ N:N cursos técnicos

    @Transactional(readOnly = true)
    public List<CursoTecnicoResponse> listarCursos(Long codigoInep) {
        return EscolaMapper.toDetalhe(obterComDetalhes(codigoInep)).cursosTecnicos();
    }

    @Transactional
    public List<CursoTecnicoResponse> adicionarCurso(Long codigoInep, Long cursoCodigo) {
        Escola escola = obterComDetalhes(codigoInep);
        CursoTecnico curso = cursoTecnicoService.obter(cursoCodigo);
        if (escola.getCursosTecnicos().contains(curso)) {
            throw new RegraDeNegocioException("A escola " + codigoInep + " já oferece o curso " + cursoCodigo + ".");
        }
        escola.adicionarCursoTecnico(curso); // insere uma linha em escola_curso_tecnico
        return cursosOrdenados(escola);
    }

    @Transactional
    public void removerCurso(Long codigoInep, Long cursoCodigo) {
        Escola escola = obterComDetalhes(codigoInep);
        CursoTecnico curso = cursoTecnicoService.obter(cursoCodigo);
        if (!escola.getCursosTecnicos().contains(curso)) {
            throw new RecursoNaoEncontradoException("A escola " + codigoInep + " não oferece o curso " + cursoCodigo + ".");
        }
        escola.removerCursoTecnico(curso); // apaga a linha em escola_curso_tecnico
    }

    // ------------------------------------------------------------ auxiliares

    private List<CursoTecnicoResponse> cursosOrdenados(Escola escola) {
        return escola.getCursosTecnicos().stream()
                .map(CursoTecnicoMapper::toResponse)
                .sorted((a, b) -> a.nome().compareTo(b.nome()))
                .toList();
    }

    private Escola obterComDetalhes(Long codigoInep) {
        return escolaRepository.findComDetalhesByCodigoInep(codigoInep)
                .orElseThrow(() -> new RecursoNaoEncontradoException("Escola " + codigoInep + " não encontrada."));
    }
}
