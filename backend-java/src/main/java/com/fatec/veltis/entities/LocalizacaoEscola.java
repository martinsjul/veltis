package com.fatec.veltis.entities;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.OneToOne;
import jakarta.persistence.Table;

/**
 * Ponto da escola no mapa (latitude e longitude em WGS 84).
 *
 * Relacionamento 1:1 com Escola. Esta classe é a DONA do relacionamento:
 * a coluna escola_codigo (FK, única) fica nesta tabela. "unique = true"
 * garante no banco que uma escola tem no máximo uma localização.
 */
@Entity
@Table(name = "localizacao_escola")
public class LocalizacaoEscola {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private Double latitude;

    @Column(nullable = false)
    private Double longitude;

    /** De onde veio o ponto: Catálogo de Escolas do INEP, SEDUC-SP ou geocodificação. */
    @Column(nullable = false, length = 120)
    private String fonte;

    /** oficial, numero, numero_aproximado ou logradouro (DEC-002). */
    @Column(nullable = false, length = 20)
    private String precisao;

    @OneToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "escola_codigo", nullable = false, unique = true)
    private Escola escola;

    public LocalizacaoEscola() {
    }

    public LocalizacaoEscola(Double latitude, Double longitude, String fonte, String precisao) {
        this.latitude = latitude;
        this.longitude = longitude;
        this.fonte = fonte;
        this.precisao = precisao;
    }

    public Long getId() {
        return id;
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

    public String getFonte() {
        return fonte;
    }

    public void setFonte(String fonte) {
        this.fonte = fonte;
    }

    public String getPrecisao() {
        return precisao;
    }

    public void setPrecisao(String precisao) {
        this.precisao = precisao;
    }

    public Escola getEscola() {
        return escola;
    }

    public void setEscola(Escola escola) {
        this.escola = escola;
    }
}
