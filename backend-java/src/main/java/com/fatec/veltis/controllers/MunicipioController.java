package com.fatec.veltis.controllers;

import java.net.URI;
import java.util.List;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.fatec.veltis.dtos.EscolaResumoResponse;
import com.fatec.veltis.dtos.MunicipioRequest;
import com.fatec.veltis.dtos.MunicipioResponse;
import com.fatec.veltis.services.MunicipioService;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Pattern;

/**
 * Endpoints dos municípios. O controller só recebe a requisição, chama o service
 * e devolve a resposta HTTP; as regras ficam no MunicipioService.
 */
@RestController
@RequestMapping("/municipios")
@Tag(name = "Municípios", description = "Os 27 municípios da Região Metropolitana de Sorocaba")
public class MunicipioController {

    private final MunicipioService service;

    public MunicipioController(MunicipioService service) {
        this.service = service;
    }

    @GetMapping
    @Operation(summary = "Lista os municípios (ordem alfabética)")
    public List<MunicipioResponse> listar() {
        return service.listar();
    }

    @GetMapping("/{codigo}")
    @Operation(summary = "Busca um município pelo código IBGE")
    public MunicipioResponse buscar(@PathVariable @Pattern(regexp = "\\d{7}", message = "Use o código IBGE com 7 dígitos.") String codigo) {
        return service.buscar(codigo);
    }

    @PostMapping
    @Operation(summary = "Cadastra um município")
    public ResponseEntity<MunicipioResponse> criar(@Valid @RequestBody MunicipioRequest dto) {
        MunicipioResponse criado = service.criar(dto);
        return ResponseEntity.created(URI.create("/municipios/" + criado.codigo())).body(criado);
    }

    @PutMapping("/{codigo}")
    @Operation(summary = "Altera um município")
    public MunicipioResponse atualizar(@PathVariable String codigo, @Valid @RequestBody MunicipioRequest dto) {
        return service.atualizar(codigo, dto);
    }

    @DeleteMapping("/{codigo}")
    @Operation(summary = "Exclui um município (só se não tiver escolas, campi nem cursos)")
    public ResponseEntity<Void> excluir(@PathVariable String codigo) {
        service.excluir(codigo);
        return ResponseEntity.noContent().build();
    }

    @GetMapping("/{codigo}/escolas")
    @Operation(summary = "Escolas do município (relacionamento 1:N), paginadas: ?page=0&size=20")
    public Page<EscolaResumoResponse> escolas(@PathVariable String codigo,
                                              @PageableDefault(size = 20, sort = "nome", direction = Sort.Direction.ASC) Pageable pageable) {
        return service.listarEscolas(codigo, pageable);
    }
}
