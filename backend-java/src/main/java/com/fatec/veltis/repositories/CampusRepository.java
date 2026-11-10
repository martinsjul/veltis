package com.fatec.veltis.repositories;

import java.util.List;

import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import com.fatec.veltis.entities.Campus;

public interface CampusRepository extends JpaRepository<Campus, Long> {

    @EntityGraph(attributePaths = {"instituicao", "municipio"})
    @Query("""
            SELECT c FROM Campus c
            WHERE (:municipio IS NULL OR c.municipio.codigo = :municipio)
              AND (:instituicao IS NULL OR c.instituicao.codigoIes = :instituicao)
            ORDER BY c.nome
            """)
    List<Campus> buscar(@Param("municipio") String municipio, @Param("instituicao") Long instituicao);

    boolean existsByMunicipioCodigo(String municipioCodigo);
}
