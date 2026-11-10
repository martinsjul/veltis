package com.fatec.veltis.controllers;

import static org.hamcrest.Matchers.hasSize;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

/**
 * Testes de ponta a ponta: sobem a aplicação com o H2 e os dados reais do seeding.
 * @Transactional desfaz o que cada teste gravou, então um teste não atrapalha o outro.
 */
@SpringBootTest
@AutoConfigureMockMvc
@Transactional
class MunicipioControllerTest {

    @Autowired
    private MockMvc mvc;

    @Test
    void listaOs27MunicipiosDaRms() throws Exception {
        mvc.perform(get("/municipios"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(27)))
                .andExpect(jsonPath("$[0].nome").value("Alambari"));
    }

    @Test
    void buscaSorocabaPeloCodigoIbge() throws Exception {
        mvc.perform(get("/municipios/3552205"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.nome").value("Sorocaba"))
                .andExpect(jsonPath("$.populacao2022").value(723682));
    }

    @Test
    void codigoInexistenteDa404() throws Exception {
        mvc.perform(get("/municipios/3500000"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.mensagem").value("Município 3500000 não encontrado."));
    }

    @Test
    void criaAlteraEExcluiUmMunicipio() throws Exception {
        String json = """
                {"codigo": "3599999", "nome": "Cidade Teste", "populacao2022": 1000, "areaKm2": 10.5}
                """;
        mvc.perform(post("/municipios").contentType(MediaType.APPLICATION_JSON).content(json))
                .andExpect(status().isCreated())
                .andExpect(header().string("Location", "/municipios/3599999"));

        mvc.perform(put("/municipios/3599999").contentType(MediaType.APPLICATION_JSON)
                        .content(json.replace("Cidade Teste", "Cidade Alterada")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.nome").value("Cidade Alterada"));

        mvc.perform(delete("/municipios/3599999")).andExpect(status().isNoContent());
        mvc.perform(get("/municipios/3599999")).andExpect(status().isNotFound());
    }

    @Test
    void validacaoDevolve400ComOsCampos() throws Exception {
        mvc.perform(post("/municipios").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"codigo\": \"123\", \"nome\": \"\"}"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.campos", hasSize(2)));
    }

    @Test
    void codigoRepetidoDa409() throws Exception {
        mvc.perform(post("/municipios").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"codigo\": \"3552205\", \"nome\": \"Sorocaba\"}"))
                .andExpect(status().isConflict());
    }

    @Test
    void naoExcluiMunicipioComEscolas() throws Exception {
        mvc.perform(delete("/municipios/3552205"))
                .andExpect(status().isConflict());
    }

    @Test
    void listaAsEscolasDoMunicipioPaginadas() throws Exception {
        mvc.perform(get("/municipios/3552205/escolas").param("size", "5"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content", hasSize(5)))
                .andExpect(jsonPath("$.content[0].municipio.nome").value("Sorocaba"))
                .andExpect(jsonPath("$.page.size").value(5));
    }
}
