package com.fatec.veltis.services;

import java.util.List;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.fatec.veltis.dtos.EscolaResumoResponse;
import com.fatec.veltis.dtos.MunicipioRequest;
import com.fatec.veltis.dtos.MunicipioResponse;
import com.fatec.veltis.entities.Municipio;
import com.fatec.veltis.exceptions.RecursoNaoEncontradoException;
import com.fatec.veltis.exceptions.RegraDeNegocioException;
import com.fatec.veltis.exceptions.RequisicaoInvalidaException;
import com.fatec.veltis.mappers.EscolaMapper;
import com.fatec.veltis.mappers.MunicipioMapper;
import com.fatec.veltis.repositories.CampusRepository;
import com.fatec.veltis.repositories.CursoSuperiorRepository;
import com.fatec.veltis.repositories.EscolaRepository;
import com.fatec.veltis.repositories.MunicipioRepository;

/** Regras de negócio dos municípios. */
@Service
public class MunicipioService {

    private final MunicipioRepository municipioRepository;
    private final EscolaRepository escolaRepository;
    private final CampusRepository campusRepository;
    private final CursoSuperiorRepository cursoSuperiorRepository;

    // Injeção de dependência pelo construtor: o Spring entrega os repositories prontos.
    public MunicipioService(MunicipioRepository municipioRepository, EscolaRepository escolaRepository,
                            CampusRepository campusRepository, CursoSuperiorRepository cursoSuperiorRepository) {
        this.municipioRepository = municipioRepository;
        this.escolaRepository = escolaRepository;
        this.campusRepository = campusRepository;
        this.cursoSuperiorRepository = cursoSuperiorRepository;
    }

    @Transactional(readOnly = true)
    public List<MunicipioResponse> listar() {
        return municipioRepository.findAllByOrderByNomeAsc().stream()
                .map(MunicipioMapper::toResponse)
                .toList();
    }

    @Transactional(readOnly = true)
    public MunicipioResponse buscar(String codigo) {
        return MunicipioMapper.toResponse(obter(codigo));
    }

    @Transactional
    public MunicipioResponse criar(MunicipioRequest dto) {
        if (municipioRepository.existsById(dto.codigo())) {
            throw new RegraDeNegocioException("Já existe um município com o código " + dto.codigo() + ".");
        }
        Municipio salvo = municipioRepository.save(MunicipioMapper.toEntity(dto));
        return MunicipioMapper.toResponse(salvo);
    }

    @Transactional
    public MunicipioResponse atualizar(String codigo, MunicipioRequest dto) {
        if (!codigo.equals(dto.codigo())) {
            throw new RequisicaoInvalidaException("O código do corpo (" + dto.codigo()
                    + ") deve ser igual ao da URL (" + codigo + "). O código IBGE não pode ser alterado.");
        }
        Municipio municipio = obter(codigo);
        MunicipioMapper.copiar(dto, municipio);
        // Dentro de @Transactional, o Hibernate grava a alteração sozinho ao final (dirty checking).
        return MunicipioMapper.toResponse(municipio);
    }

    /** Regra: não apaga município que ainda tem escolas, campi ou cursos (integridade referencial). */
    @Transactional
    public void excluir(String codigo) {
        Municipio municipio = obter(codigo);
        if (escolaRepository.existsByMunicipioCodigo(codigo)
                || campusRepository.existsByMunicipioCodigo(codigo)
                || cursoSuperiorRepository.existsByMunicipioCodigo(codigo)) {
            throw new RegraDeNegocioException("O município " + municipio.getNome()
                    + " tem escolas, campi ou cursos ligados a ele e não pode ser excluído.");
        }
        municipioRepository.delete(municipio);
    }

    /** Navegação 1:N: as escolas do município, paginadas. */
    @Transactional(readOnly = true)
    public Page<EscolaResumoResponse> listarEscolas(String codigo, Pageable pageable) {
        obter(codigo);
        return escolaRepository.buscar(codigo, null, null, pageable).map(EscolaMapper::toResumo);
    }

    Municipio obter(String codigo) {
        return municipioRepository.findById(codigo)
                .orElseThrow(() -> new RecursoNaoEncontradoException("Município " + codigo + " não encontrado."));
    }
}
