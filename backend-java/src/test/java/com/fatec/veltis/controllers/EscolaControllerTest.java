package com.fatec.veltis.controllers;

import static org.hamcrest.Matchers.hasItem;
import static org.hamcrest.Matchers.not;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
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
class EscolaControllerTest {

    private static final String NOVA_ESCOLA = """
            {
              "codigoInep": 99999999,
              "nome": "ETEC Teste Veltis",
              "municipioCodigo": "3552205",
              "dependencia": "ESTADUAL",
              "situacao": "EM_ATIVIDADE",
              "cep": "18040810",
              "ofereceEnsinoMedio": true
            }
            """;

    @Autowired
    private MockMvc mvc;

    @Test
    void fichaDaEtecFernandoPrestesTrazOsRelacionamentos() throws Exception {
        mvc.perform(get("/escolas/35016238"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.tipo").value("ETEC"))
                .andExpect(jsonPath("$.municipio.nome").value("Sorocaba"))
                .andExpect(jsonPath("$.localizacao.latitude").isNumber())
                .andExpect(jsonPath("$.cursosTecnicos[*].nome").value(hasItem("Desenvolvimento de Sistemas")));
    }

    @Test
    void filtraPorMunicipioDependenciaENome() throws Exception {
        mvc.perform(get("/escolas").param("municipio", "3552205").param("dependencia", "estadual").param("nome", "etec"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content[*].tipo").value(not(hasItem("Escola"))));
    }

    @Test
    void parametrosInvalidosDao400() throws Exception {
        mvc.perform(get("/escolas").param("municipio", "abc")).andExpect(status().isBadRequest());
        mvc.perform(get("/escolas").param("dependencia", "particular")).andExpect(status().isBadRequest());
        mvc.perform(get("/escolas").param("sort", "cor")).andExpect(status().isBadRequest());
        mvc.perform(get("/escolas/abc")).andExpect(status().isBadRequest());
    }

    @Test
    void crudCompletoDaEscola() throws Exception {
        mvc.perform(post("/escolas").contentType(MediaType.APPLICATION_JSON).content(NOVA_ESCOLA))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.tipo").value("ETEC"))
                .andExpect(jsonPath("$.municipio.codigo").value("3552205"));

        mvc.perform(put("/escolas/99999999").contentType(MediaType.APPLICATION_JSON)
                        .content(NOVA_ESCOLA.replace("EM_ATIVIDADE", "PARALISADA")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.situacao").value("PARALISADA"));

        mvc.perform(delete("/escolas/99999999")).andExpect(status().isNoContent());
        mvc.perform(get("/escolas/99999999")).andExpect(status().isNotFound());
    }

    @Test
    void escolaComMunicipioInexistenteDa404() throws Exception {
        mvc.perform(post("/escolas").contentType(MediaType.APPLICATION_JSON)
                        .content(NOVA_ESCOLA.replace("3552205", "3500000")))
                .andExpect(status().isNotFound());
    }

    @Test
    void codigoDoCorpoDiferenteDaUrlDa400() throws Exception {
        mvc.perform(put("/escolas/35016238").contentType(MediaType.APPLICATION_JSON).content(NOVA_ESCOLA))
                .andExpect(status().isBadRequest());
    }

    @Test
    void localizacaoUmParaUm() throws Exception {
        mvc.perform(post("/escolas").contentType(MediaType.APPLICATION_JSON).content(NOVA_ESCOLA))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.localizacao").doesNotExist());

        String ponto = "{\"latitude\": -23.51, \"longitude\": -47.47, \"fonte\": \"Teste\", \"precisao\": \"numero\"}";
        mvc.perform(put("/escolas/99999999/localizacao").contentType(MediaType.APPLICATION_JSON).content(ponto))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.precisao").value("numero"));

        // latitude e longitude trocadas: fora do estado de SP
        String trocado = "{\"latitude\": -47.47, \"longitude\": -23.51, \"fonte\": \"Teste\", \"precisao\": \"numero\"}";
        mvc.perform(put("/escolas/99999999/localizacao").contentType(MediaType.APPLICATION_JSON).content(trocado))
                .andExpect(status().isBadRequest());

        mvc.perform(delete("/escolas/99999999/localizacao")).andExpect(status().isNoContent());
        mvc.perform(get("/escolas/99999999")).andExpect(jsonPath("$.localizacao").doesNotExist());
    }

    @Test
    void associaERemoveCursoTecnicoMuitosParaMuitos() throws Exception {
        mvc.perform(post("/escolas").contentType(MediaType.APPLICATION_JSON).content(NOVA_ESCOLA))
                .andExpect(status().isCreated());

        mvc.perform(post("/escolas/99999999/cursos-tecnicos/6082"))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$[0].nome").value("Desenvolvimento de Sistemas"));

        // a mesma associação de novo: 409
        mvc.perform(post("/escolas/99999999/cursos-tecnicos/6082")).andExpect(status().isConflict());

        // o outro lado do N:N enxerga a escola nova
        mvc.perform(get("/cursos-tecnicos/6082/escolas"))
                .andExpect(jsonPath("$[*].codigoInep").value(hasItem(99999999)));

        mvc.perform(delete("/escolas/99999999/cursos-tecnicos/6082")).andExpect(status().isNoContent());
        mvc.perform(get("/escolas/99999999/cursos-tecnicos")).andExpect(jsonPath("$").isEmpty());
    }

    @Test
    void excluirCursoTiraDasEscolasMasNaoApagaAEscola() throws Exception {
        mvc.perform(delete("/cursos-tecnicos/6082")).andExpect(status().isNoContent());
        mvc.perform(get("/escolas/35016238"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.cursosTecnicos[*].codigo").value(not(hasItem(6082))));
    }
}
