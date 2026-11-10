package com.fatec.veltis.entities;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

import com.fatec.veltis.enums.Dependencia;

/** Testes unitários das regras que ficam nas próprias entidades (sem banco). */
class RegrasDoDominioTest {

    @Test
    void etecEEscolaEstadualComNomeEtec() {
        Escola e = new Escola();
        e.setNome("ETEC FERNANDO PRESTES");
        e.setDependencia(Dependencia.ESTADUAL);
        assertTrue(e.isEtec());

        e.setDependencia(Dependencia.PRIVADA);
        assertFalse(e.isEtec());

        e.setDependencia(Dependencia.ESTADUAL);
        e.setNome("EE PROFESSOR ETECILDO");
        assertFalse(e.isEtec());
    }

    @Test
    void fatecPelaSiglaOuPeloNome() {
        InstituicaoEnsinoSuperior i = new InstituicaoEnsinoSuperior();
        i.setNome("FACULDADE DE TECNOLOGIA DE SOROCABA");
        i.setSigla("FATEC SO");
        assertTrue(i.isFatec());

        i.setSigla("FAMO");
        i.setNome("FACULDADE DE TECNOLOGIA E MODA");
        assertFalse(i.isFatec());
    }

    @Test
    void associacaoMuitosParaMuitosAtualizaOsDoisLados() {
        Escola e = new Escola();
        e.setCodigoInep(1L);
        CursoTecnico c = new CursoTecnico(10L, "Informática", "Informação e comunicação");

        e.adicionarCursoTecnico(c);
        assertTrue(c.getEscolas().contains(e));

        e.removerCursoTecnico(c);
        assertFalse(c.getEscolas().contains(e));
        assertEquals(0, e.getCursosTecnicos().size());
    }

    @Test
    void localizacaoUmParaUmApontaDeVoltaParaAEscola() {
        Escola e = new Escola();
        LocalizacaoEscola l = new LocalizacaoEscola(-23.5, -47.4, "Teste", "oficial");
        e.definirLocalizacao(l);
        assertSame(e, l.getEscola());

        e.definirLocalizacao(null);
        assertNull(e.getLocalizacao());
        assertNull(l.getEscola());
    }
}
