package com.fatec.veltis.dtos;

/** Município resumido, usado dentro de outros JSONs (escola, campus...). Evita ciclos. */
public record MunicipioResumoResponse(String codigo, String nome) {
}
