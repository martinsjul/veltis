package com.fatec.veltis;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.data.web.config.EnableSpringDataWebSupport;

/**
 * Ponto de entrada do backend Java do Veltis.
 *
 * Rodar: ./mvnw spring-boot:run  (Windows: mvnw.cmd spring-boot:run)
 * Swagger:    http://localhost:8080/swagger-ui.html
 * Console H2: http://localhost:8080/h2-console
 */
@SpringBootApplication
// Faz as respostas paginadas (Page) virarem um JSON estável: { content: [...], page: {...} }
@EnableSpringDataWebSupport(pageSerializationMode = EnableSpringDataWebSupport.PageSerializationMode.VIA_DTO)
public class VeltisApplication {

    public static void main(String[] args) {
        SpringApplication.run(VeltisApplication.class, args);
    }
}
