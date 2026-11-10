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
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.fatec.veltis.dtos.CursoSuperiorRequest;
import com.fatec.veltis.dtos.CursoSuperiorResponse;
import com.fatec.veltis.services.CursoSuperiorService;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Pattern;

@RestController
@RequestMapping("/cursos-superiores")
@Tag(name = "Cursos superiores", description = "Graduações presenciais por município de oferta")
public class CursoSuperiorController {

    private final CursoSuperiorService service;

    public CursoSuperiorController(CursoSuperiorService service) {
        this.service = service;
    }

    @GetMapping
    @Operation(summary = "Lista cursos (filtros opcionais: ?municipio=3552205&instituicao=33)")
    public List<CursoSuperiorResponse> listar(
            @RequestParam(required = false) @Pattern(regexp = "\\d{7}", message = "Use o código IBGE com 7 dígitos.") String municipio,
            @RequestParam(required = false) Long instituicao) {
        return service.listar(municipio, instituicao);
    }

    @GetMapping("/{id}")
    @Operation(summary = "Busca um curso superior")
    public CursoSuperiorResponse buscar(@PathVariable Long id) {
        return service.buscar(id);
    }

    @PostMapping
    @Operation(summary = "Cadastra um curso (associa instituição e município pelos códigos)")
    public ResponseEntity<CursoSuperiorResponse> criar(@Valid @RequestBody CursoSuperiorRequest dto) {
        CursoSuperiorResponse criado = service.criar(dto);
        return ResponseEntity.created(URI.create("/cursos-superiores/" + criado.id())).body(criado);
    }

    @PutMapping("/{id}")
    @Operation(summary = "Altera um curso superior")
    public CursoSuperiorResponse atualizar(@PathVariable Long id, @Valid @RequestBody CursoSuperiorRequest dto) {
        return service.atualizar(id, dto);
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "Exclui um curso superior")
    public ResponseEntity<Void> excluir(@PathVariable Long id) {
        service.excluir(id);
        return ResponseEntity.noContent().build();
    }
}
