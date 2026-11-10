package com.fatec.veltis.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;

/** Título e descrição que aparecem no Swagger UI. */
@Configuration
public class OpenApiConfig {

    @Bean
    public OpenAPI veltisOpenApi() {
        return new OpenAPI().info(new Info()
                .title("API Veltis — Java/Spring Boot")
                .version("1.0.0")
                .description("""
                        Backend Java do Projeto Integrador Veltis (ADS — Fatec Sorocaba).
                        Escolas, faculdades, cursos e municípios da Região Metropolitana de Sorocaba,
                        com dados reais do IBGE e do INEP carregados no banco H2 ao iniciar.
                        """));
    }
}
