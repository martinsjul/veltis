package com.fatec.veltis.controllers;

import static org.hamcrest.Matchers.everyItem;
import static org.hamcrest.Matchers.hasSize;
import static org.hamcrest.Matchers.is;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

@SpringBootTest
@AutoConfigureMockMvc
@Transactional
class InstituicaoECampusControllerTest {

    @Autowired
    private MockMvc mvc;

    @Test
    void fatecSorocabaTemUmCampusComCoordenada() throws Exception {
        mvc.perform(get("/instituicoes/33"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.tipo").value("FATEC"))
                .andExpect(jsonPath("$.quantidadeCampi").value(1));

        mvc.perform(get("/instituicoes/33/campi"))
                .andExpect(jsonPath("$", hasSize(1)))
                .andExpect(jsonPath("$[0].latitude").value(-23.480133))
                .andExpect(jsonPath("$[0].municipio.nome").value("Sorocaba"));
    }

    @Test
    void cursosDaInstituicaoNoMunicipioDeOferta() throws Exception {
        mvc.perform(get("/cursos-superiores").param("instituicao", "33"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[*].municipio.codigo", everyItem(is("3552205"))));
    }

    @Test
    void criaCampusAssociandoInstituicaoEMunicipio() throws Exception {
        String json = """
                {"nome": "Fatec Sorocaba - Unidade 2", "instituicaoCodigo": 33, "municipioCodigo": "3552205",
                 "latitude": -23.49, "longitude": -47.44, "precisao": "NUMERO"}
                """;
        mvc.perform(post("/campi").contentType(MediaType.APPLICATION_JSON).content(json))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.instituicao.sigla").value("FATEC SO"));

        mvc.perform(get("/instituicoes/33/campi")).andExpect(jsonPath("$", hasSize(2)));
    }

    @Test
    void campusComInstituicaoInexistenteDa404() throws Exception {
        String json = """
                {"nome": "Campus X", "instituicaoCodigo": 999999, "municipioCodigo": "3552205",
                 "latitude": -23.49, "longitude": -47.44, "precisao": "RUA"}
                """;
        mvc.perform(post("/campi").contentType(MediaType.APPLICATION_JSON).content(json))
                .andExpect(status().isNotFound());
    }

    @Test
    void enumInvalidoNoJsonDa400() throws Exception {
        String json = """
                {"codigoIes": 999999, "nome": "Faculdade Teste", "rede": "MISTA"}
                """;
        mvc.perform(post("/instituicoes").contentType(MediaType.APPLICATION_JSON).content(json))
                .andExpect(status().isBadRequest());
    }

    @Test
    void excluirInstituicaoApagaCampiECursosEmCascata() throws Exception {
        mvc.perform(delete("/instituicoes/33")).andExpect(status().isNoContent());
        mvc.perform(get("/campi").param("instituicao", "33")).andExpect(jsonPath("$").isEmpty());
        mvc.perform(get("/cursos-superiores").param("instituicao", "33")).andExpect(jsonPath("$").isEmpty());
    }

    @Test
    void cursoComCodigoEmecRepetidoDa409() throws Exception {
        String json = """
                {"codigoEmec": 112680, "nome": "Repetido", "instituicaoCodigo": 7, "municipioCodigo": "3552205"}
                """;
        mvc.perform(post("/cursos-superiores").contentType(MediaType.APPLICATION_JSON).content(json))
                .andExpect(status().isConflict());
    }
}
