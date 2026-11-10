package com.fatec.veltis.repositories;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;

import com.fatec.veltis.entities.CursoTecnico;

public interface CursoTecnicoRepository extends JpaRepository<CursoTecnico, Long> {

    List<CursoTecnico> findAllByOrderByNomeAsc();
}
