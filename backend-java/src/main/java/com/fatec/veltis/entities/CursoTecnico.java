package com.fatec.veltis.entities;

import java.util.HashSet;
import java.util.Objects;
import java.util.Set;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.ManyToMany;
import jakarta.persistence.Table;

/**
 * Curso técnico do catálogo do INEP (ex.: Técnico em Informática).
 *
 * N:N com Escola: um curso é oferecido por várias escolas e uma escola
 * oferece vários cursos. Aqui é o lado INVERSO (mappedBy): a tabela de
 * junção escola_curso_tecnico é controlada pela Escola.
 */
@Entity
@Table(name = "curso_tecnico")
public class CursoTecnico {

    /** Código do curso no Censo Escolar. */
    @Id
    private Long codigo;

    @Column(nullable = false, length = 150)
    private String nome;

    /** Área profissional (ex.: Informação e Comunicação). */
    @Column(length = 150)
    private String area;

    @ManyToMany(mappedBy = "cursosTecnicos")
    private Set<Escola> escolas = new HashSet<>();

    public CursoTecnico() {
    }

    public CursoTecnico(Long codigo, String nome, String area) {
        this.codigo = codigo;
        this.nome = nome;
        this.area = area;
    }

    public Long getCodigo() {
        return codigo;
    }

    public void setCodigo(Long codigo) {
        this.codigo = codigo;
    }

    public String getNome() {
        return nome;
    }

    public void setNome(String nome) {
        this.nome = nome;
    }

    public String getArea() {
        return area;
    }

    public void setArea(String area) {
        this.area = area;
    }

    public Set<Escola> getEscolas() {
        return escolas;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) {
            return true;
        }
        if (!(o instanceof CursoTecnico outro)) {
            return false;
        }
        return codigo != null && codigo.equals(outro.codigo);
    }

    @Override
    public int hashCode() {
        return Objects.hashCode(codigo);
    }
}
