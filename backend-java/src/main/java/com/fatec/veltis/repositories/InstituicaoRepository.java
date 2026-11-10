package com.fatec.veltis.repositories;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;

import com.fatec.veltis.entities.InstituicaoEnsinoSuperior;

public interface InstituicaoRepository extends JpaRepository<InstituicaoEnsinoSuperior, Long> {

    List<InstituicaoEnsinoSuperior> findAllByOrderByNomeAsc();
}
