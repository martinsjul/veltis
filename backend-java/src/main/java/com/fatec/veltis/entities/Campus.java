package com.fatec.veltis.entities;

import com.fatec.veltis.enums.PrecisaoCampus;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;

/**
 * Local de oferta (campus) de uma instituição de ensino superior, com latitude e longitude.
 *
 * O INEP não publica coordenadas das faculdades; os 39 campi da RMS foram
 * levantados pela equipe (DEC-001).
 *
 * Relacionamentos (esta classe é a DONA dos dois):
 *  - N:1 com InstituicaoEnsinoSuperior (FK instituicao_codigo)
 *  - N:1 com Municipio                 (FK municipio_codigo)
 */
@Entity
@Table(name = "campus",
       uniqueConstraints = @UniqueConstraint(columnNames = {"instituicao_codigo", "municipio_codigo", "nome"}))
public class Campus {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 150)
    private String nome;

    @Column(length = 200)
    private String endereco;

    @Column(length = 100)
    private String bairro;

    @Column(length = 8)
    private String cep;

    @Column(nullable = false)
    private Double latitude;

    @Column(nullable = false)
    private Double longitude;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 10)
    private PrecisaoCampus precisao;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "instituicao_codigo", nullable = false)
    private InstituicaoEnsinoSuperior instituicao;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "municipio_codigo", nullable = false)
    private Municipio municipio;

    public Campus() {
    }

    public Long getId() {
        return id;
    }

    public String getNome() {
        return nome;
    }

    public void setNome(String nome) {
        this.nome = nome;
    }

    public String getEndereco() {
        return endereco;
    }

    public void setEndereco(String endereco) {
        this.endereco = endereco;
    }

    public String getBairro() {
        return bairro;
    }

    public void setBairro(String bairro) {
        this.bairro = bairro;
    }

    public String getCep() {
        return cep;
    }

    public void setCep(String cep) {
        this.cep = cep;
    }

    public Double getLatitude() {
        return latitude;
    }

    public void setLatitude(Double latitude) {
        this.latitude = latitude;
    }

    public Double getLongitude() {
        return longitude;
    }

    public void setLongitude(Double longitude) {
        this.longitude = longitude;
    }

    public PrecisaoCampus getPrecisao() {
        return precisao;
    }

    public void setPrecisao(PrecisaoCampus precisao) {
        this.precisao = precisao;
    }

    public InstituicaoEnsinoSuperior getInstituicao() {
        return instituicao;
    }

    public void setInstituicao(InstituicaoEnsinoSuperior instituicao) {
        this.instituicao = instituicao;
    }

    public Municipio getMunicipio() {
        return municipio;
    }

    public void setMunicipio(Municipio municipio) {
        this.municipio = municipio;
    }
}
