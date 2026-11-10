package com.fatec.veltis.banco;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;

/** Confere no H2 as tabelas e chaves estrangeiras que o README manda mostrar na apresentação. */
@SpringBootTest
class ConsultasDoReadmeTest {

    @Autowired
    private JdbcTemplate jdbc;

    @Test
    void hibernateCriouAsOitoChavesEstrangeiras() {
        List<Map<String, Object>> fks = jdbc.queryForList("""
                SELECT TABLE_NAME, CONSTRAINT_NAME FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
                WHERE CONSTRAINT_TYPE = 'FOREIGN KEY' ORDER BY TABLE_NAME""");
        assertEquals(8, fks.size());
    }

    @Test
    void tabelaDeJuncaoTemOsCursosDaEtecFernandoPrestes() {
        List<String> cursos = jdbc.queryForList("""
                SELECT c.nome FROM escola_curso_tecnico ec
                JOIN escola e ON e.codigo_inep = ec.escola_codigo
                JOIN curso_tecnico c ON c.codigo = ec.curso_codigo
                WHERE ec.escola_codigo = 35016238""", String.class);
        assertTrue(cursos.contains("Desenvolvimento de Sistemas"));
    }

    @Test
    void escolasPorMunicipio() {
        List<Map<String, Object>> linhas = jdbc.queryForList("""
                SELECT m.nome, COUNT(e.codigo_inep) AS escolas
                FROM municipio m LEFT JOIN escola e ON e.municipio_codigo = m.codigo
                GROUP BY m.nome ORDER BY escolas DESC""");
        assertEquals(27, linhas.size());
        assertEquals("Sorocaba", linhas.get(0).get("NOME"));
    }
}
