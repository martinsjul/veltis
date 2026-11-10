package com.fatec.veltis.controllers;

import java.util.Map;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import io.swagger.v3.oas.annotations.Hidden;

/** Página inicial da API: mostra onde estão a documentação e o console do banco. */
@RestController
@Hidden
public class InicioController {

    @GetMapping("/")
    public Map<String, String> inicio() {
        return Map.of(
                "api", "Veltis (Java/Spring Boot)",
                "documentacao", "/swagger-ui.html",
                "bancoH2", "/h2-console");
    }
}
