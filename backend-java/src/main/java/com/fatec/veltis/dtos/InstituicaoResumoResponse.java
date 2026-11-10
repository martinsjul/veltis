package com.fatec.veltis.dtos;

/** Instituição resumida, usada dentro do JSON de campus e de curso. */
public record InstituicaoResumoResponse(Long codigoIes, String nome, String sigla) {
}
