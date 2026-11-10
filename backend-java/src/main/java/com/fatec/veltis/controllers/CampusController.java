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

import com.fatec.veltis.dtos.CampusRequest;
import com.fatec.veltis.dtos.CampusResponse;
import com.fatec.veltis.services.CampusService;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Pattern;

@RestController
@RequestMapping("/campi")
@Tag(name = "Campi", description = "Locais de oferta das faculdades, com latitude e longitude")
public class CampusController {

    private final CampusService service;

    public CampusController(CampusService service) {
        this.service = service;
    }

    @GetMapping
    @Operation(summary = "Lista campi (filtros opcionais: ?municipio=3552205&instituicao=33)")
    public List<CampusResponse> listar(
            @RequestParam(required = false) @Pattern(regexp = "\\d{7}", message = "Use o código IBGE com 7 dígitos.") String municipio,
            @RequestParam(required = false) Long instituicao) {
        return service.listar(municipio, instituicao);
    }

    @GetMapping("/{id}")
    @Operation(summary = "Busca um campus")
    public CampusResponse buscar(@PathVariable Long id) {
        return service.buscar(id);
    }

    @PostMapping
    @Operation(summary = "Cadastra um campus (associa instituição e município pelos códigos)")
    public ResponseEntity<CampusResponse> criar(@Valid @RequestBody CampusRequest dto) {
        CampusResponse criado = service.criar(dto);
        return ResponseEntity.created(URI.create("/campi/" + criado.id())).body(criado);
    }

    @PutMapping("/{id}")
    @Operation(summary = "Altera um campus")
    public CampusResponse atualizar(@PathVariable Long id, @Valid @RequestBody CampusRequest dto) {
        return service.atualizar(id, dto);
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "Exclui um campus")
    public ResponseEntity<Void> excluir(@PathVariable Long id) {
        service.excluir(id);
        return ResponseEntity.noContent().build();
    }
}
