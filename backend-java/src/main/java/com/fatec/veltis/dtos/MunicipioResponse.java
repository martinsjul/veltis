package com.fatec.veltis.dtos;

/** JSON de saída de um município. */
public record MunicipioResponse(String codigo, String nome, Long populacao2022, Double areaKm2) {
}
