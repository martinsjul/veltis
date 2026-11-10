package com.fatec.veltis.entities;

import com.fatec.veltis.enums.GrauAcademico;

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

/**
 * Curso de graduação presencial oferecido por uma instituição em um município.
 *
 * Regra RN-09: o município do curso é o LOCAL DE OFERTA, não a sede da instituição.
 *
 * Relacionamentos (esta classe é a DONA dos dois):
 *  - N:1 com InstituicaoEnsinoSuperior (FK instituicao_codigo)
 *  - N:1 com Municipio                 (FK municipio_codigo)
 */
@Entity
@Table(name = "curso_superior")
public class CursoSuperior {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /** Código do curso no e-MEC/INEP (co_curso). Único. */
    @Column(name = "codigo_emec", nullable = false, unique = true)
    private Long codigoEmec;

    @Column(nullable = false, length = 150)
    private String nome;

    @Enumerated(EnumType.STRING)
    @Column(length = 30)
    private GrauAcademico grau;

    /** Área geral CINE (classificação internacional). */
    @Column(length = 150)
    private String area;

    private Boolean gratuito;

    private Integer vagas;

    private Integer matriculas;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "instituicao_codigo", nullable = false)
    private InstituicaoEnsinoSuperior instituicao;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "municipio_codigo", nullable = false)
    private Municipio municipio;

    public CursoSuperior() {
    }

    public Long getId() {
        return id;
    }

    public Long getCodigoEmec() {
        return codigoEmec;
    }

    public void setCodigoEmec(Long codigoEmec) {
        this.codigoEmec = codigoEmec;
    }

    public String getNome() {
        return nome;
    }

    public void setNome(String nome) {
        this.nome = nome;
    }

    public GrauAcademico getGrau() {
        return grau;
    }

    public void setGrau(GrauAcademico grau) {
        this.grau = grau;
    }

    public String getArea() {
        return area;
    }

    public void setArea(String area) {
        this.area = area;
    }

    public Boolean getGratuito() {
        return gratuito;
    }

    public void setGratuito(Boolean gratuito) {
        this.gratuito = gratuito;
    }

    public Integer getVagas() {
        return vagas;
    }

    public void setVagas(Integer vagas) {
        this.vagas = vagas;
    }

    public Integer getMatriculas() {
        return matriculas;
    }

    public void setMatriculas(Integer matriculas) {
        this.matriculas = matriculas;
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
