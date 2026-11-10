package com.fatec.veltis.seed;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import com.fatec.veltis.entities.Campus;
import com.fatec.veltis.entities.CursoSuperior;
import com.fatec.veltis.entities.CursoTecnico;
import com.fatec.veltis.entities.Escola;
import com.fatec.veltis.entities.InstituicaoEnsinoSuperior;
import com.fatec.veltis.entities.LocalizacaoEscola;
import com.fatec.veltis.entities.Municipio;
import com.fatec.veltis.enums.Dependencia;
import com.fatec.veltis.enums.GrauAcademico;
import com.fatec.veltis.enums.PrecisaoCampus;
import com.fatec.veltis.enums.Rede;
import com.fatec.veltis.enums.SituacaoFuncionamento;
import com.fatec.veltis.repositories.CursoTecnicoRepository;
import com.fatec.veltis.repositories.EscolaRepository;
import com.fatec.veltis.repositories.InstituicaoRepository;
import com.fatec.veltis.repositories.MunicipioRepository;

/**
 * Seeding: ao iniciar a aplicação, carrega no H2 os dados REAIS da RMS que
 * estão em src/main/resources/seed (exportados do banco do Veltis):
 *
 *   municipios.csv            27 municípios (IBGE, Censo 2022)
 *   cursos_tecnicos.csv       catálogo de cursos técnicos (Censo Escolar 2025)
 *   escolas.csv               1.806 escolas (Censo Escolar 2025)
 *   localizacoes_escolas.csv  pontos oficiais (Catálogo de Escolas do INEP / SEDUC-SP)
 *   escola_curso_tecnico.csv  quais escolas oferecem quais cursos (N:N)
 *   instituicoes.csv          faculdades com curso presencial na RMS (Censo Superior 2024)
 *   campi.csv                 39 campi com latitude e longitude (levantamento da equipe)
 *   cursos_superiores.csv     cursos presenciais por município de oferta
 *
 * Só roda se o banco estiver vazio, então reiniciar não duplica nada.
 */
@Component
@ConditionalOnProperty(name = "veltis.seed.ativo", havingValue = "true", matchIfMissing = true)
public class DadosIniciais implements CommandLineRunner {

    private static final Logger log = LoggerFactory.getLogger(DadosIniciais.class);

    private final MunicipioRepository municipioRepository;
    private final CursoTecnicoRepository cursoTecnicoRepository;
    private final EscolaRepository escolaRepository;
    private final InstituicaoRepository instituicaoRepository;

    public DadosIniciais(MunicipioRepository municipioRepository, CursoTecnicoRepository cursoTecnicoRepository,
                         EscolaRepository escolaRepository, InstituicaoRepository instituicaoRepository) {
        this.municipioRepository = municipioRepository;
        this.cursoTecnicoRepository = cursoTecnicoRepository;
        this.escolaRepository = escolaRepository;
        this.instituicaoRepository = instituicaoRepository;
    }

    @Override
    @Transactional
    public void run(String... args) {
        if (municipioRepository.count() > 0) {
            log.info("Banco já tem dados; o seeding foi pulado.");
            return;
        }

        // 1) Municípios
        Map<String, Municipio> municipios = new HashMap<>();
        for (Map<String, String> l : LeitorCsv.ler("municipios.csv")) {
            Municipio m = new Municipio(l.get("codigo"), l.get("nome"),
                    longOuNulo(l.get("populacao_2022")), doubleOuNulo(l.get("area_km2")));
            municipios.put(m.getCodigo(), m);
        }
        municipioRepository.saveAll(municipios.values());

        // 2) Cursos técnicos
        Map<Long, CursoTecnico> cursos = new HashMap<>();
        for (Map<String, String> l : LeitorCsv.ler("cursos_tecnicos.csv")) {
            CursoTecnico c = new CursoTecnico(Long.valueOf(l.get("codigo")), l.get("nome"), l.get("area"));
            cursos.put(c.getCodigo(), c);
        }
        cursoTecnicoRepository.saveAll(cursos.values());

        // 3) Escolas (N:1 com município)
        Map<Long, Escola> escolas = new HashMap<>();
        for (Map<String, String> l : LeitorCsv.ler("escolas.csv")) {
            Escola e = new Escola();
            e.setCodigoInep(Long.valueOf(l.get("codigo_inep")));
            e.setNome(l.get("nome"));
            e.setMunicipio(municipios.get(l.get("municipio_codigo")));
            e.setDependencia(Dependencia.doRotulo(l.get("dependencia")));
            e.setSituacao(SituacaoFuncionamento.doRotulo(l.get("situacao")));
            e.setEndereco(cortar(l.get("endereco"), 200));
            e.setCep(l.get("cep"));
            e.setTelefone(cortar(l.get("telefone"), 20));
            e.setOfereceEnsinoMedio("t".equals(l.get("oferece_ensino_medio")));
            escolas.put(e.getCodigoInep(), e);
        }

        // 4) Localização (1:1) — cascade ALL na Escola salva a localização junto
        for (Map<String, String> l : LeitorCsv.ler("localizacoes_escolas.csv")) {
            Escola e = escolas.get(Long.valueOf(l.get("escola_codigo")));
            e.definirLocalizacao(new LocalizacaoEscola(Double.valueOf(l.get("latitude")),
                    Double.valueOf(l.get("longitude")), l.get("fonte"), "oficial"));
        }

        // 5) Cursos técnicos de cada escola (N:N)
        for (Map<String, String> l : LeitorCsv.ler("escola_curso_tecnico.csv")) {
            escolas.get(Long.valueOf(l.get("escola_codigo")))
                    .adicionarCursoTecnico(cursos.get(Long.valueOf(l.get("curso_codigo"))));
        }
        escolaRepository.saveAll(escolas.values());

        // 6) Instituições, campi e cursos superiores (1:N com cascade)
        Map<Long, InstituicaoEnsinoSuperior> instituicoes = new HashMap<>();
        for (Map<String, String> l : LeitorCsv.ler("instituicoes.csv")) {
            InstituicaoEnsinoSuperior i = new InstituicaoEnsinoSuperior();
            i.setCodigoIes(Long.valueOf(l.get("codigo")));
            i.setNome(l.get("nome"));
            i.setSigla(l.get("sigla"));
            i.setRede(Rede.doRotulo(l.get("rede")));
            i.setOrganizacaoAcademica(l.get("organizacao_academica"));
            instituicoes.put(i.getCodigoIes(), i);
        }
        for (Map<String, String> l : LeitorCsv.ler("campi.csv")) {
            Campus c = new Campus();
            c.setNome(l.get("nome"));
            c.setEndereco(l.get("endereco"));
            c.setBairro(l.get("bairro"));
            c.setCep(l.get("cep"));
            c.setLatitude(Double.valueOf(l.get("latitude")));
            c.setLongitude(Double.valueOf(l.get("longitude")));
            c.setPrecisao(PrecisaoCampus.doValor(l.get("precisao")));
            c.setMunicipio(municipios.get(l.get("municipio_codigo")));
            instituicoes.get(Long.valueOf(l.get("instituicao_codigo"))).adicionarCampus(c);
        }
        for (Map<String, String> l : LeitorCsv.ler("cursos_superiores.csv")) {
            CursoSuperior c = new CursoSuperior();
            c.setCodigoEmec(Long.valueOf(l.get("codigo_emec")));
            c.setNome(l.get("nome"));
            c.setGrau(GrauAcademico.doRotulo(l.get("grau")));
            c.setArea(l.get("area"));
            c.setGratuito(l.get("gratuito") == null ? null : "t".equals(l.get("gratuito")));
            c.setVagas(intOuNulo(l.get("vagas")));
            c.setMatriculas(intOuNulo(l.get("matriculas")));
            c.setMunicipio(municipios.get(l.get("municipio_codigo")));
            instituicoes.get(Long.valueOf(l.get("instituicao_codigo"))).adicionarCurso(c);
        }
        instituicaoRepository.saveAll(instituicoes.values());

        List<Integer> totais = List.of(municipios.size(), escolas.size(), cursos.size(), instituicoes.size());
        log.info("Seeding concluído: {} municípios, {} escolas, {} cursos técnicos, {} instituições.",
                totais.get(0), totais.get(1), totais.get(2), totais.get(3));
    }

    private static Long longOuNulo(String s) {
        return s == null ? null : Long.valueOf(s);
    }

    private static Integer intOuNulo(String s) {
        return s == null ? null : Integer.valueOf(s);
    }

    private static Double doubleOuNulo(String s) {
        return s == null ? null : Double.valueOf(s);
    }

    private static String cortar(String s, int max) {
        return (s == null || s.length() <= max) ? s : s.substring(0, max);
    }
}
