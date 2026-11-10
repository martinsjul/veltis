package com.fatec.veltis.repositories;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;

import com.fatec.veltis.entities.Municipio;

/**
 * Acesso à tabela municipio. O JpaRepository já traz save, findById, findAll,
 * deleteById, existsById... sem escrever SQL.
 */
public interface MunicipioRepository extends JpaRepository<Municipio, String> {

    /** O Spring cria a consulta pelo nome do método: ORDER BY nome. */
    List<Municipio> findAllByOrderByNomeAsc();
}
