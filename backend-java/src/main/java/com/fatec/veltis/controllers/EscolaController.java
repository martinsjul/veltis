package com.fatec.veltis.controllers;

import java.net.URI;
import java.util.List;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.HttpStatus;
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

import com.fatec.veltis.dtos.CursoTecnicoResponse;
import com.fatec.veltis.dtos.EscolaDetalheResponse;
import com.fatec.veltis.dtos.EscolaRequest;
import com.fatec.veltis.dtos.EscolaResumoResponse;
import com.fatec.veltis.dtos.LocalizacaoRequest;
import com.fatec.veltis.dtos.LocalizacaoResponse;
import com.fatec.veltis.enums.Dependencia;
import com.fatec.veltis.services.EscolaService;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

@RestController
@RequestMapping("/escolas")
@Tag(name = "Escolas", description = "Escolas do Censo Escolar, localização (1:1) e cursos técnicos (N:N)")
public class EscolaController {

    private final EscolaService service;

    public EscolaController(EscolaService service) {
        this.service = service;
    }

    // ------------------------------------------------------------ CRUD

    @GetMapping
    @Operation(summary = "Lista escolas com filtros opcionais e paginação (?page=0&size=20&sort=nome)")
    public Page<EscolaResumoResponse> listar(
            @RequestParam(required = false) @Pattern(regexp = "\\d{7}", message = "Use o código IBGE com 7 dígitos.") String municipio,
            @RequestParam(required = false) Dependencia dependencia,
            @RequestParam(required = false) @Size(min = 2, max = 100, message = "A busca deve ter de 2 a 100 caracteres.") String nome,
            @PageableDefault(size = 20, sort = "nome", direction = Sort.Direction.ASC) Pageable pageable) {
        return service.listar(municipio, dependencia, nome, pageable);
    }

    @GetMapping("/{codigoInep}")
    @Operation(summary = "Ficha da escola com município, localização e cursos técnicos")
    public EscolaDetalheResponse buscar(@PathVariable Long codigoInep) {
        return service.buscar(codigoInep);
    }

    @PostMapping
    @Operation(summary = "Cadastra uma escola (associa ao município pelo municipioCodigo)")
    public ResponseEntity<EscolaDetalheResponse> criar(@Valid @RequestBody EscolaRequest dto) {
        EscolaDetalheResponse criada = service.criar(dto);
        return ResponseEntity.created(URI.create("/escolas/" + criada.codigoInep())).body(criada);
    }

    @PutMapping("/{codigoInep}")
    @Operation(summary = "Altera uma escola")
    public EscolaDetalheResponse atualizar(@PathVariable Long codigoInep, @Valid @RequestBody EscolaRequest dto) {
        return service.atualizar(codigoInep, dto);
    }

    @DeleteMapping("/{codigoInep}")
    @Operation(summary = "Exclui uma escola (a localização vai junto; os cursos continuam)")
    public ResponseEntity<Void> excluir(@PathVariable Long codigoInep) {
        service.excluir(codigoInep);
        return ResponseEntity.noContent().build();
    }

    // ------------------------------------------------------------ 1:1 localização

    @PutMapping("/{codigoInep}/localizacao")
    @Operation(summary = "Cria ou troca o ponto da escola no mapa (relacionamento 1:1)")
    public LocalizacaoResponse definirLocalizacao(@PathVariable Long codigoInep, @Valid @RequestBody LocalizacaoRequest dto) {
        return service.definirLocalizacao(codigoInep, dto);
    }

    @DeleteMapping("/{codigoInep}/localizacao")
    @Operation(summary = "Remove o ponto da escola")
    public ResponseEntity<Void> removerLocalizacao(@PathVariable Long codigoInep) {
        service.removerLocalizacao(codigoInep);
        return ResponseEntity.noContent().build();
    }

    // ------------------------------------------------------------ N:N cursos técnicos

    @GetMapping("/{codigoInep}/cursos-tecnicos")
    @Operation(summary = "Cursos técnicos oferecidos pela escola (relacionamento N:N)")
    public List<CursoTecnicoResponse> cursos(@PathVariable Long codigoInep) {
        return service.listarCursos(codigoInep);
    }

    @PostMapping("/{codigoInep}/cursos-tecnicos/{cursoCodigo}")
    @Operation(summary = "Associa um curso técnico à escola (insere em escola_curso_tecnico)")
    public ResponseEntity<List<CursoTecnicoResponse>> adicionarCurso(@PathVariable Long codigoInep,
                                                                     @PathVariable Long cursoCodigo) {
        return ResponseEntity.status(HttpStatus.CREATED).body(service.adicionarCurso(codigoInep, cursoCodigo));
    }

    @DeleteMapping("/{codigoInep}/cursos-tecnicos/{cursoCodigo}")
    @Operation(summary = "Remove a associação entre a escola e o curso")
    public ResponseEntity<Void> removerCurso(@PathVariable Long codigoInep, @PathVariable Long cursoCodigo) {
        service.removerCurso(codigoInep, cursoCodigo);
        return ResponseEntity.noContent().build();
    }
}
