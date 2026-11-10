package com.fatec.veltis.services;

import java.util.List;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.fatec.veltis.dtos.CursoSuperiorRequest;
import com.fatec.veltis.dtos.CursoSuperiorResponse;
import com.fatec.veltis.entities.CursoSuperior;
import com.fatec.veltis.exceptions.RecursoNaoEncontradoException;
import com.fatec.veltis.exceptions.RegraDeNegocioException;
import com.fatec.veltis.mappers.CursoSuperiorMapper;
import com.fatec.veltis.repositories.CursoSuperiorRepository;

@Service
public class CursoSuperiorService {

    private final CursoSuperiorRepository cursoSuperiorRepository;
    private final InstituicaoService instituicaoService;
    private final MunicipioService municipioService;

    public CursoSuperiorService(CursoSuperiorRepository cursoSuperiorRepository,
                                InstituicaoService instituicaoService, MunicipioService municipioService) {
        this.cursoSuperiorRepository = cursoSuperiorRepository;
        this.instituicaoService = instituicaoService;
        this.municipioService = municipioService;
    }

    @Transactional(readOnly = true)
    public List<CursoSuperiorResponse> listar(String municipio, Long instituicao) {
        return cursoSuperiorRepository.buscar(municipio, instituicao).stream()
                .map(CursoSuperiorMapper::toResponse)
                .toList();
    }

    @Transactional(readOnly = true)
    public CursoSuperiorResponse buscar(Long id) {
        return CursoSuperiorMapper.toResponse(obter(id));
    }

    @Transactional
    public CursoSuperiorResponse criar(CursoSuperiorRequest dto) {
        if (cursoSuperiorRepository.existsByCodigoEmec(dto.codigoEmec())) {
            throw new RegraDeNegocioException("Já existe um curso com o código e-MEC " + dto.codigoEmec() + ".");
        }
        CursoSuperior curso = CursoSuperiorMapper.toEntity(dto);
        curso.setMunicipio(municipioService.obter(dto.municipioCodigo()));
        instituicaoService.obter(dto.instituicaoCodigo()).adicionarCurso(curso);
        return CursoSuperiorMapper.toResponse(cursoSuperiorRepository.save(curso));
    }

    @Transactional
    public CursoSuperiorResponse atualizar(Long id, CursoSuperiorRequest dto) {
        CursoSuperior curso = obter(id);
        if (!curso.getCodigoEmec().equals(dto.codigoEmec()) && cursoSuperiorRepository.existsByCodigoEmec(dto.codigoEmec())) {
            throw new RegraDeNegocioException("Já existe um curso com o código e-MEC " + dto.codigoEmec() + ".");
        }
        CursoSuperiorMapper.copiar(dto, curso);
        curso.setMunicipio(municipioService.obter(dto.municipioCodigo()));
        curso.setInstituicao(instituicaoService.obter(dto.instituicaoCodigo()));
        cursoSuperiorRepository.flush();
        return CursoSuperiorMapper.toResponse(curso);
    }

    @Transactional
    public void excluir(Long id) {
        CursoSuperior curso = obter(id);
        curso.getInstituicao().getCursos().remove(curso);
        cursoSuperiorRepository.delete(curso);
    }

    private CursoSuperior obter(Long id) {
        return cursoSuperiorRepository.findById(id)
                .orElseThrow(() -> new RecursoNaoEncontradoException("Curso superior " + id + " não encontrado."));
    }
}
