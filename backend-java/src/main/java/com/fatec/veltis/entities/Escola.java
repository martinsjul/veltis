package com.fatec.veltis.entities;

import java.util.HashSet;
import java.util.Objects;
import java.util.Set;

import com.fatec.veltis.enums.Dependencia;
import com.fatec.veltis.enums.SituacaoFuncionamento;

import jakarta.persistence.CascadeType;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.JoinTable;
import jakarta.persistence.ManyToMany;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.OneToOne;
import jakarta.persistence.Table;

/**
 * Escola do Censo Escolar (INEP).
 *
 * Relacionamentos:
 *  - N:1 com Municipio   (chave estrangeira municipio_codigo nesta tabela)
 *  - 1:1 com LocalizacaoEscola (a chave estrangeira fica na tabela da localização)
 *  - N:N com CursoTecnico (tabela de junção escola_curso_tecnico; a Escola é a dona)
 */
@Entity
@Table(name = "escola")
public class Escola {

    /** Código INEP da escola: vem da fonte oficial, por isso não é gerado pelo banco. */
    @Id
    @Column(name = "codigo_inep")
    private Long codigoInep;

    @Column(nullable = false, length = 150)
    private String nome;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private Dependencia dependencia;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private SituacaoFuncionamento situacao;

    @Column(length = 200)
    private String endereco;

    @Column(length = 8)
    private String cep;

    @Column(length = 20)
    private String telefone;

    @Column(name = "oferece_ensino_medio", nullable = false)
    private boolean ofereceEnsinoMedio;

    /**
     * Lado dono do relacionamento N:1. Cria a coluna municipio_codigo (FK para municipio.codigo).
     * LAZY: o município só é buscado no banco quando alguém usa getMunicipio().
     */
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "municipio_codigo", nullable = false)
    private Municipio municipio;

    /**
     * Lado inverso do 1:1. A FK escola_codigo fica na tabela localizacao_escola.
     * cascade ALL + orphanRemoval: salvar/apagar a escola salva/apaga a localização junto.
     */
    @OneToOne(mappedBy = "escola", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.LAZY)
    private LocalizacaoEscola localizacao;

    /**
     * Lado dono do N:N. @JoinTable descreve a tabela de junção:
     * escola_curso_tecnico (escola_codigo -> escola, curso_codigo -> curso_tecnico).
     */
    @ManyToMany
    @JoinTable(
            name = "escola_curso_tecnico",
            joinColumns = @JoinColumn(name = "escola_codigo"),
            inverseJoinColumns = @JoinColumn(name = "curso_codigo"))
    private Set<CursoTecnico> cursosTecnicos = new HashSet<>();

    public Escola() {
    }

    // ------------------------------------------------------------ regras do domínio

    /** ETECs aparecem no Censo como escolas estaduais cujo nome começa com "ETEC ". */
    public boolean isEtec() {
        return dependencia == Dependencia.ESTADUAL && nome != null && nome.toUpperCase().startsWith("ETEC ");
    }

    public boolean isEmAtividade() {
        return situacao == SituacaoFuncionamento.EM_ATIVIDADE;
    }

    /** Mantém os dois lados do N:N em sincronia. */
    public void adicionarCursoTecnico(CursoTecnico curso) {
        cursosTecnicos.add(curso);
        curso.getEscolas().add(this);
    }

    public void removerCursoTecnico(CursoTecnico curso) {
        cursosTecnicos.remove(curso);
        curso.getEscolas().remove(this);
    }

    /** Liga a localização à escola (os dois lados do 1:1). null remove a localização. */
    public void definirLocalizacao(LocalizacaoEscola nova) {
        if (nova == null) {
            if (this.localizacao != null) {
                this.localizacao.setEscola(null);
            }
        } else {
            nova.setEscola(this);
        }
        this.localizacao = nova;
    }

    // ------------------------------------------------------------ getters e setters

    public Long getCodigoInep() {
        return codigoInep;
    }

    public void setCodigoInep(Long codigoInep) {
        this.codigoInep = codigoInep;
    }

    public String getNome() {
        return nome;
    }

    public void setNome(String nome) {
        this.nome = nome;
    }

    public Dependencia getDependencia() {
        return dependencia;
    }

    public void setDependencia(Dependencia dependencia) {
        this.dependencia = dependencia;
    }

    public SituacaoFuncionamento getSituacao() {
        return situacao;
    }

    public void setSituacao(SituacaoFuncionamento situacao) {
        this.situacao = situacao;
    }

    public String getEndereco() {
        return endereco;
    }

    public void setEndereco(String endereco) {
        this.endereco = endereco;
    }

    public String getCep() {
        return cep;
    }

    public void setCep(String cep) {
        this.cep = cep;
    }

    public String getTelefone() {
        return telefone;
    }

    public void setTelefone(String telefone) {
        this.telefone = telefone;
    }

    public boolean isOfereceEnsinoMedio() {
        return ofereceEnsinoMedio;
    }

    public void setOfereceEnsinoMedio(boolean ofereceEnsinoMedio) {
        this.ofereceEnsinoMedio = ofereceEnsinoMedio;
    }

    public Municipio getMunicipio() {
        return municipio;
    }

    public void setMunicipio(Municipio municipio) {
        this.municipio = municipio;
    }

    public LocalizacaoEscola getLocalizacao() {
        return localizacao;
    }

    public Set<CursoTecnico> getCursosTecnicos() {
        return cursosTecnicos;
    }

    // Duas escolas são a mesma se têm o mesmo código INEP (necessário para o Set do N:N).
    @Override
    public boolean equals(Object o) {
        if (this == o) {
            return true;
        }
        if (!(o instanceof Escola outra)) {
            return false;
        }
        return codigoInep != null && codigoInep.equals(outra.codigoInep);
    }

    @Override
    public int hashCode() {
        return Objects.hashCode(codigoInep);
    }
}
