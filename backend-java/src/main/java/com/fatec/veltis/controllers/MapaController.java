package com.fatec.veltis.controllers;

import java.util.List;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.fatec.veltis.dtos.InstituicaoNoMapaResponse;
import com.fatec.veltis.services.MapaService;
import com.fatec.veltis.services.MapaService.TipoNoMapa;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.constraints.Pattern;

@RestController
@RequestMapping("/mapa")
@Tag(name = "Mapa", description = "Escolas e faculdades com latitude e longitude para os pinos do site")
public class MapaController {

    private final MapaService service;

    public MapaController(MapaService service) {
        this.service = service;
    }

    @GetMapping("/instituicoes")
    @Operation(summary = "Escolas e faculdades com latitude e longitude",
               description = "Mesmo formato da API Python do Veltis. Filtros: ?municipio=3552205&tipo=etec&tipo=fatec")
    public List<InstituicaoNoMapaResponse> instituicoes(
            @RequestParam(required = false) @Pattern(regexp = "\\d{7}", message = "Use o código IBGE com 7 dígitos.") String municipio,
            @RequestParam(required = false) List<TipoNoMapa> tipo,
            @RequestParam(name = "apenas_ativas", defaultValue = "true") boolean apenasAtivas) {
        return service.instituicoes(municipio, tipo, apenasAtivas);
    }
}
