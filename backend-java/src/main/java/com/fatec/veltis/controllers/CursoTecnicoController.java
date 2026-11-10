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

import com.fatec.veltis.dtos.CursoTecnicoRequest;
import com.fatec.veltis.dtos.CursoTecnicoResponse;
import com.fatec.veltis.dtos.EscolaResumoResponse;
import com.fatec.veltis.services.CursoTecnicoService;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;

@RestController
@RequestMapping("/cursos-tecnicos")
@Tag(name = "Cursos técnicos", description = "Catálogo de cursos técnicos (lado inverso do N:N com Escola)")
public class CursoTecnicoController {

    private final CursoTecnicoService service;

    public CursoTecnicoController(CursoTecnicoService service) {
        this.service = service;
    }

    @GetMapping
    @Operation(summary = "Lista os cursos técnicos")
    public List<CursoTecnicoResponse> listar() {
        return service.listar();
    }

    @GetMapping("/{codigo}")
    @Operation(summary = "Busca um curso técnico")
    public CursoTecnicoResponse buscar(@PathVariable Long codigo) {
        return service.buscar(codigo);
    }

    @PostMapping
    @Operation(summary = "Cadastra um curso técnico")
    public ResponseEntity<CursoTecnicoResponse> criar(@Valid @RequestBody CursoTecnicoRequest dto) {
        CursoTecnicoResponse criado = service.criar(dto);
        return ResponseEntity.created(URI.create("/cursos-tecnicos/" + criado.codigo())).body(criado);
    }

    @PutMapping("/{codigo}")
    @Operation(summary = "Altera um curso técnico")
    public CursoTecnicoResponse atualizar(@PathVariable Long codigo, @Valid @RequestBody CursoTecnicoRequest dto) {
        return service.atualizar(codigo, dto);
    }

    @DeleteMapping("/{codigo}")
    @Operation(summary = "Exclui o curso (antes tira o curso de todas as escolas)")
    public ResponseEntity<Void> excluir(@PathVariable Long codigo) {
        service.excluir(codigo);
        return ResponseEntity.noContent().build();
    }

    @GetMapping("/{codigo}/escolas")
    @Operation(summary = "Escolas que oferecem o curso (navegação pelo lado inverso do N:N)")
    public List<EscolaResumoResponse> escolas(@PathVariable Long codigo) {
        return service.listarEscolas(codigo);
    }
}
