package com.fatec.veltis.repositories;

import java.util.List;
import java.util.Optional;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import com.fatec.veltis.entities.Escola;
import com.fatec.veltis.enums.Dependencia;

public interface EscolaRepository extends JpaRepository<Escola, Long> {

    /**
     * Lista com filtros opcionais (null = sem filtro).
     * @EntityGraph busca o município junto, numa consulta só (evita o problema N+1).
     */
    @EntityGraph(attributePaths = {"municipio", "localizacao"})
    @Query("""
            SELECT e FROM Escola e
            WHERE (:municipio IS NULL OR e.municipio.codigo = :municipio)
              AND (:dependencia IS NULL OR e.dependencia = :dependencia)
              AND (:nome IS NULL OR LOWER(e.nome) LIKE LOWER(CONCAT('%', :nome, '%')))
            """)
    Page<Escola> buscar(@Param("municipio") String municipio,
                        @Param("dependencia") Dependencia dependencia,
                        @Param("nome") String nome,
                        Pageable pageable);

    /** Ficha da escola com município, localização e cursos técnicos já carregados. */
    @EntityGraph(attributePaths = {"municipio", "localizacao", "cursosTecnicos"})
    Optional<Escola> findComDetalhesByCodigoInep(Long codigoInep);

    /** Escolas com ponto no mapa (as que têm localização), para o endpoint /mapa. */
    @EntityGraph(attributePaths = {"municipio", "localizacao", "cursosTecnicos"})
    @Query("""
            SELECT e FROM Escola e
            WHERE e.localizacao IS NOT NULL
              AND (:municipio IS NULL OR e.municipio.codigo = :municipio)
            """)
    List<Escola> buscarComLocalizacao(@Param("municipio") String municipio);

    boolean existsByMunicipioCodigo(String municipioCodigo);
}
