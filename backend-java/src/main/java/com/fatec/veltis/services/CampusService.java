package com.fatec.veltis.services;

import java.util.List;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.fatec.veltis.dtos.CampusRequest;
import com.fatec.veltis.dtos.CampusResponse;
import com.fatec.veltis.entities.Campus;
import com.fatec.veltis.exceptions.RecursoNaoEncontradoException;
import com.fatec.veltis.mappers.CampusMapper;
import com.fatec.veltis.repositories.CampusRepository;

@Service
public class CampusService {

    private final CampusRepository campusRepository;
    private final InstituicaoService instituicaoService;
    private final MunicipioService municipioService;

    public CampusService(CampusRepository campusRepository, InstituicaoService instituicaoService,
                         MunicipioService municipioService) {
        this.campusRepository = campusRepository;
        this.instituicaoService = instituicaoService;
        this.municipioService = municipioService;
    }

    @Transactional(readOnly = true)
    public List<CampusResponse> listar(String municipio, Long instituicao) {
        return campusRepository.buscar(municipio, instituicao).stream()
                .map(CampusMapper::toResponse)
                .toList();
    }

    @Transactional(readOnly = true)
    public CampusResponse buscar(Long id) {
        return CampusMapper.toResponse(obter(id));
    }

    /**
     * Cria o campus e faz as duas associações N:1 a partir dos códigos do JSON.
     * Se a instituição ou o município não existem, devolve 404 (não cria campus "solto").
     */
    @Transactional
    public CampusResponse criar(CampusRequest dto) {
        Campus campus = CampusMapper.toEntity(dto);
        campus.setMunicipio(municipioService.obter(dto.municipioCodigo()));
        instituicaoService.obter(dto.instituicaoCodigo()).adicionarCampus(campus);
        return CampusMapper.toResponse(campusRepository.save(campus));
    }

    @Transactional
    public CampusResponse atualizar(Long id, CampusRequest dto) {
        Campus campus = obter(id);
        CampusMapper.copiar(dto, campus);
        campus.setMunicipio(municipioService.obter(dto.municipioCodigo()));
        campus.setInstituicao(instituicaoService.obter(dto.instituicaoCodigo()));
        campusRepository.flush();
        return CampusMapper.toResponse(campus);
    }

    @Transactional
    public void excluir(Long id) {
        Campus campus = obter(id);
        campus.getInstituicao().getCampi().remove(campus);
        campusRepository.delete(campus);
    }

    private Campus obter(Long id) {
        return campusRepository.findById(id)
                .orElseThrow(() -> new RecursoNaoEncontradoException("Campus " + id + " não encontrado."));
    }
}
