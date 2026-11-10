package com.fatec.veltis.entities;

import java.util.ArrayList;
import java.util.List;

import com.fatec.veltis.enums.Rede;

import jakarta.persistence.CascadeType;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Id;
import jakarta.persistence.OneToMany;
import jakarta.persistence.Table;

/**
 * Faculdade, centro universitário, universidade ou instituto federal (Censo da Educação Superior).
 *
 * 1:N com Campus e 1:N com CursoSuperior. Esta classe é o lado INVERSO dos dois:
 * as chaves estrangeiras (instituicao_codigo) ficam nas tabelas campus e curso_superior.
 */
@Entity
@Table(name = "instituicao_ensino_superior")
public class InstituicaoEnsinoSuperior {

    /** Código da instituição no INEP (co_ies). */
    @Id
    @Column(name = "codigo_ies")
    private Long codigoIes;

    @Column(nullable = false, length = 200)
    private String nome;

    @Column(length = 30)
    private String sigla;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 10)
    private Rede rede;

    /** Faculdade, Centro Universitário, Universidade ou Instituto Federal. */
    @Column(name = "organizacao_academica", length = 50)
    private String organizacaoAcademica;

    /** Apagar a instituição apaga seus campi (cascade + orphanRemoval). */
    @OneToMany(mappedBy = "instituicao", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<Campus> campi = new ArrayList<>();

    /** Apagar a instituição apaga seus cursos. */
    @OneToMany(mappedBy = "instituicao", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<CursoSuperior> cursos = new ArrayList<>();

    public InstituicaoEnsinoSuperior() {
    }

    /** Regra do Veltis: é FATEC quando "FATEC" aparece na sigla ou no nome. */
    public boolean isFatec() {
        String texto = ((sigla == null ? "" : sigla) + " " + nome).toUpperCase();
        return texto.contains("FATEC");
    }

    public void adicionarCampus(Campus campus) {
        campi.add(campus);
        campus.setInstituicao(this);
    }

    public void adicionarCurso(CursoSuperior curso) {
        cursos.add(curso);
        curso.setInstituicao(this);
    }

    public Long getCodigoIes() {
        return codigoIes;
    }

    public void setCodigoIes(Long codigoIes) {
        this.codigoIes = codigoIes;
    }

    public String getNome() {
        return nome;
    }

    public void setNome(String nome) {
        this.nome = nome;
    }

    public String getSigla() {
        return sigla;
    }

    public void setSigla(String sigla) {
        this.sigla = sigla;
    }

    public Rede getRede() {
        return rede;
    }

    public void setRede(Rede rede) {
        this.rede = rede;
    }

    public String getOrganizacaoAcademica() {
        return organizacaoAcademica;
    }

    public void setOrganizacaoAcademica(String organizacaoAcademica) {
        this.organizacaoAcademica = organizacaoAcademica;
    }

    public List<Campus> getCampi() {
        return campi;
    }

    public List<CursoSuperior> getCursos() {
        return cursos;
    }
}
