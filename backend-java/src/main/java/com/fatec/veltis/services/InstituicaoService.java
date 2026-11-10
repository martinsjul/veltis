package com.fatec.veltis.services;

import java.util.Comparator;
import java.util.List;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.fatec.veltis.dtos.CampusResponse;
import com.fatec.veltis.dtos.CursoSuperiorResponse;
import com.fatec.veltis.dtos.InstituicaoRequest;
import com.fatec.veltis.dtos.InstituicaoResponse;
import com.fatec.veltis.entities.Campus;
import com.fatec.veltis.entities.CursoSuperior;
import com.fatec.veltis.entities.InstituicaoEnsinoSuperior;
import com.fatec.veltis.exceptions.RecursoNaoEncontradoException;
import com.fatec.veltis.exceptions.RegraDeNegocioException;
import com.fatec.veltis.exceptions.RequisicaoInvalidaException;
import com.fatec.veltis.mappers.CampusMapper;
import com.fatec.veltis.mappers.CursoSuperiorMapper;
import com.fatec.veltis.mappers.InstituicaoMapper;
import com.fatec.veltis.repositories.InstituicaoRepository;

@Service
public class InstituicaoService {

    private final InstituicaoRepository instituicaoRepository;

    public InstituicaoService(InstituicaoRepository instituicaoRepository) {
        this.instituicaoRepository = instituicaoRepository;
    }

    @Transactional(readOnly = true)
    public List<InstituicaoResponse> listar() {
        return instituicaoRepository.findAllByOrderByNomeAsc().stream()
                .map(InstituicaoMapper::toResponse)
                .toList();
    }

    @Transactional(readOnly = true)
    public InstituicaoResponse buscar(Long codigoIes) {
        return InstituicaoMapper.toResponse(obter(codigoIes));
    }

    @Transactional
    public InstituicaoResponse criar(InstituicaoRequest dto) {
        if (instituicaoRepository.existsById(dto.codigoIes())) {
            throw new RegraDeNegocioException("Já existe uma instituição com o código " + dto.codigoIes() + ".");
        }
        return InstituicaoMapper.toResponse(instituicaoRepository.save(InstituicaoMapper.toEntity(dto)));
    }

    @Transactional
    public InstituicaoResponse atualizar(Long codigoIes, InstituicaoRequest dto) {
        if (!codigoIes.equals(dto.codigoIes())) {
            throw new RequisicaoInvalidaException("O código do corpo (" + dto.codigoIes()
                    + ") deve ser igual ao da URL (" + codigoIes + ").");
        }
        InstituicaoEnsinoSuperior instituicao = obter(codigoIes);
        InstituicaoMapper.copiar(dto, instituicao);
        return InstituicaoMapper.toResponse(instituicao);
    }

    /** Regra: apagar a instituição apaga também seus campi e cursos (cascade no 1:N). */
    @Transactional
    public void excluir(Long codigoIes) {
        instituicaoRepository.delete(obter(codigoIes));
    }

    /** Navegação 1:N: campi da instituição. */
    @Transactional(readOnly = true)
    public List<CampusResponse> listarCampi(Long codigoIes) {
        return obter(codigoIes).getCampi().stream()
                .sorted(Comparator.comparing(Campus::getNome))
                .map(CampusMapper::toResponse)
                .toList();
    }

    /** Navegação 1:N: cursos superiores da instituição. */
    @Transactional(readOnly = true)
    public List<CursoSuperiorResponse> listarCursos(Long codigoIes) {
        return obter(codigoIes).getCursos().stream()
                .sorted(Comparator.comparing(CursoSuperior::getNome))
                .map(CursoSuperiorMapper::toResponse)
                .toList();
    }

    InstituicaoEnsinoSuperior obter(Long codigoIes) {
        return instituicaoRepository.findById(codigoIes)
                .orElseThrow(() -> new RecursoNaoEncontradoException("Instituição " + codigoIes + " não encontrada."));
    }
}
