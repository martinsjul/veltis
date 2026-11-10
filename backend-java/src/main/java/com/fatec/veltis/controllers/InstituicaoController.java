package com.fatec.veltis.controllers;

import java.net.URI;
import java.util.List;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.fatec.veltis.dtos.CampusResponse;
import com.fatec.veltis.dtos.CursoSuperiorResponse;
import com.fatec.veltis.dtos.InstituicaoRequest;
import com.fatec.veltis.dtos.InstituicaoResponse;
import com.fatec.veltis.services.InstituicaoService;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;

@RestController
@RequestMapping("/instituicoes")
@Tag(name = "Instituições de ensino superior", description = "Faculdades e universidades (1:N com campi e cursos)")
public class InstituicaoController {

    private final InstituicaoService service;

    public InstituicaoController(InstituicaoService service) {
        this.service = service;
    }

    @GetMapping
    @Operation(summary = "Lista as instituições com curso presencial na RMS")
    public List<InstituicaoResponse> listar() {
        return service.listar();
    }

    @GetMapping("/{codigoIes}")
    @Operation(summary = "Busca uma instituição")
    public InstituicaoResponse buscar(@PathVariable Long codigoIes) {
        return service.buscar(codigoIes);
    }

    @PostMapping
    @Operation(summary = "Cadastra uma instituição")
    public ResponseEntity<InstituicaoResponse> criar(@Valid @RequestBody InstituicaoRequest dto) {
        InstituicaoResponse criada = service.criar(dto);
        return ResponseEntity.created(URI.create("/instituicoes/" + criada.codigoIes())).body(criada);
    }

    @PutMapping("/{codigoIes}")
    @Operation(summary = "Altera uma instituição")
    public InstituicaoResponse atualizar(@PathVariable Long codigoIes, @Valid @RequestBody InstituicaoRequest dto) {
        return service.atualizar(codigoIes, dto);
    }

    @DeleteMapping("/{codigoIes}")
    @Operation(summary = "Exclui a instituição e, em cascata, seus campi e cursos")
    public ResponseEntity<Void> excluir(@PathVariable Long codigoIes) {
        service.excluir(codigoIes);
        return ResponseEntity.noContent().build();
    }

    @GetMapping("/{codigoIes}/campi")
    @Operation(summary = "Campi da instituição, com latitude e longitude (1:N)")
    public List<CampusResponse> campi(@PathVariable Long codigoIes) {
        return service.listarCampi(codigoIes);
    }

    @GetMapping("/{codigoIes}/cursos")
    @Operation(summary = "Cursos superiores da instituição (1:N)")
    public List<CursoSuperiorResponse> cursos(@PathVariable Long codigoIes) {
        return service.listarCursos(codigoIes);
    }
}
