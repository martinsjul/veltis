package com.fatec.veltis.services;

import java.util.Comparator;
import java.util.List;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.fatec.veltis.dtos.CursoTecnicoRequest;
import com.fatec.veltis.dtos.CursoTecnicoResponse;
import com.fatec.veltis.dtos.EscolaResumoResponse;
import com.fatec.veltis.entities.CursoTecnico;
import com.fatec.veltis.entities.Escola;
import com.fatec.veltis.exceptions.RecursoNaoEncontradoException;
import com.fatec.veltis.exceptions.RegraDeNegocioException;
import com.fatec.veltis.exceptions.RequisicaoInvalidaException;
import com.fatec.veltis.mappers.CursoTecnicoMapper;
import com.fatec.veltis.mappers.EscolaMapper;
import com.fatec.veltis.repositories.CursoTecnicoRepository;

@Service
public class CursoTecnicoService {

    private final CursoTecnicoRepository cursoTecnicoRepository;

    public CursoTecnicoService(CursoTecnicoRepository cursoTecnicoRepository) {
        this.cursoTecnicoRepository = cursoTecnicoRepository;
    }

    @Transactional(readOnly = true)
    public List<CursoTecnicoResponse> listar() {
        return cursoTecnicoRepository.findAllByOrderByNomeAsc().stream()
                .map(CursoTecnicoMapper::toResponse)
                .toList();
    }

    @Transactional(readOnly = true)
    public CursoTecnicoResponse buscar(Long codigo) {
        return CursoTecnicoMapper.toResponse(obter(codigo));
    }

    @Transactional
    public CursoTecnicoResponse criar(CursoTecnicoRequest dto) {
        if (cursoTecnicoRepository.existsById(dto.codigo())) {
            throw new RegraDeNegocioException("Já existe um curso técnico com o código " + dto.codigo() + ".");
        }
        return CursoTecnicoMapper.toResponse(cursoTecnicoRepository.save(CursoTecnicoMapper.toEntity(dto)));
    }

    @Transactional
    public CursoTecnicoResponse atualizar(Long codigo, CursoTecnicoRequest dto) {
        if (!codigo.equals(dto.codigo())) {
            throw new RequisicaoInvalidaException("O código do corpo (" + dto.codigo()
                    + ") deve ser igual ao da URL (" + codigo + ").");
        }
        CursoTecnico curso = obter(codigo);
        CursoTecnicoMapper.copiar(dto, curso);
        return CursoTecnicoMapper.toResponse(curso);
    }

    /**
     * O curso está do lado INVERSO do N:N: antes de apagá-lo é preciso tirar
     * o curso de cada escola (lado dono), senão a FK da tabela de junção impede.
     */
    @Transactional
    public void excluir(Long codigo) {
        CursoTecnico curso = obter(codigo);
        for (Escola escola : List.copyOf(curso.getEscolas())) {
            escola.removerCursoTecnico(curso);
        }
        cursoTecnicoRepository.delete(curso);
    }

    /** Navegação pelo lado inverso do N:N: quais escolas oferecem este curso. */
    @Transactional(readOnly = true)
    public List<EscolaResumoResponse> listarEscolas(Long codigo) {
        return obter(codigo).getEscolas().stream()
                .sorted(Comparator.comparing(Escola::getNome))
                .map(EscolaMapper::toResumo)
                .toList();
    }

    CursoTecnico obter(Long codigo) {
        return cursoTecnicoRepository.findById(codigo)
                .orElseThrow(() -> new RecursoNaoEncontradoException("Curso técnico " + codigo + " não encontrado."));
    }
}
