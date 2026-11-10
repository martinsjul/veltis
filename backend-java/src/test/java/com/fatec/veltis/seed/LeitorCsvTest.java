package com.fatec.veltis.seed;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.util.List;

import org.junit.jupiter.api.Test;

class LeitorCsvTest {

    @Test
    void separaCamposComAspasEPontoEVirgula() {
        assertEquals(List.of("1", "Rua A; 10", "x\"y", ""), LeitorCsv.separar("1;\"Rua A; 10\";\"x\"\"y\";"));
    }

    @Test
    void leOsMunicipiosDoSeed() {
        assertEquals(27, LeitorCsv.ler("municipios.csv").size());
    }
}
