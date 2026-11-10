package com.fatec.veltis.controllers;

import static org.hamcrest.Matchers.everyItem;
import static org.hamcrest.Matchers.greaterThan;
import static org.hamcrest.Matchers.is;
import static org.hamcrest.Matchers.notNullValue;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.test.web.servlet.MockMvc;

@SpringBootTest
@AutoConfigureMockMvc
class MapaControllerTest {

    @Autowired
    private MockMvc mvc;

    @Test
    void todosOsItensTemLatitudeELongitude() throws Exception {
        mvc.perform(get("/mapa/instituicoes"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.length()", greaterThan(1500)))
                .andExpect(jsonPath("$[*].latitude", everyItem(notNullValue())))
                .andExpect(jsonPath("$[*].longitude", everyItem(notNullValue())));
    }

    @Test
    void filtraPorTipoEMunicipio() throws Exception {
        mvc.perform(get("/mapa/instituicoes").param("municipio", "3552205").param("tipo", "fatec"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].nome").value("Fatec Sorocaba"))
                .andExpect(jsonPath("$[0].cep").value("18013-280"))
                .andExpect(jsonPath("$[0].precisaoLocalizacao").value("edificio"))
                .andExpect(jsonPath("$[*].tipo", everyItem(is("FATEC"))));

        mvc.perform(get("/mapa/instituicoes").param("tipo", "etec"))
                .andExpect(jsonPath("$[*].tipo", everyItem(is("ETEC"))));
    }

    @Test
    void tipoInvalidoDa400() throws Exception {
        mvc.perform(get("/mapa/instituicoes").param("tipo", "creche"))
                .andExpect(status().isBadRequest());
    }
}
