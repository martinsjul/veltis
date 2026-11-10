package com.fatec.veltis.entities;

import java.util.ArrayList;
import java.util.List;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.OneToMany;
import jakarta.persistence.Table;

/**
 * Município da Região Metropolitana de Sorocaba (IBGE).
 *
 * A chave primária é o código IBGE de 7 dígitos (ex.: 3552205 = Sorocaba),
 * o mesmo código usado em todas as fontes oficiais.
 */
@Entity
@Table(name = "municipio")
public class Municipio {

    @Id
    @Column(length = 7)
    private String codigo;

    @Column(nullable = false, length = 100)
    private String nome;

    @Column(name = "populacao_2022")
    private Long populacao2022;

    @Column(name = "area_km2")
    private Double areaKm2;

    /**
     * Lado inverso do relacionamento 1:N com Escola.
     * "mappedBy" diz que quem guarda a chave estrangeira é o campo "municipio" da Escola.
     */
    @OneToMany(mappedBy = "municipio")
    private List<Escola> escolas = new ArrayList<>();

    /** Campi de faculdades que ficam neste município (lado inverso). */
    @OneToMany(mappedBy = "municipio")
    private List<Campus> campi = new ArrayList<>();

    public Municipio() {
    }

    public Municipio(String codigo, String nome, Long populacao2022, Double areaKm2) {
        this.codigo = codigo;
        this.nome = nome;
        this.populacao2022 = populacao2022;
        this.areaKm2 = areaKm2;
    }

    public String getCodigo() {
        return codigo;
    }

    public void setCodigo(String codigo) {
        this.codigo = codigo;
    }

    public String getNome() {
        return nome;
    }

    public void setNome(String nome) {
        this.nome = nome;
    }

    public Long getPopulacao2022() {
        return populacao2022;
    }

    public void setPopulacao2022(Long populacao2022) {
        this.populacao2022 = populacao2022;
    }

    public Double getAreaKm2() {
        return areaKm2;
    }

    public void setAreaKm2(Double areaKm2) {
        this.areaKm2 = areaKm2;
    }

    public List<Escola> getEscolas() {
        return escolas;
    }

    public List<Campus> getCampi() {
        return campi;
    }
}
