package com.fatec.veltis.dtos;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.PositiveOrZero;
import jakarta.validation.constraints.Size;

/** JSON de entrada para criar ou alterar um município. */
public record MunicipioRequest(

        @NotBlank(message = "O código IBGE é obrigatório.")
        @Pattern(regexp = "\\d{7}", message = "O código IBGE deve ter 7 dígitos (ex.: 3552205).")
        String codigo,

        @NotBlank(message = "O nome é obrigatório.")
        @Size(max = 100, message = "O nome pode ter no máximo 100 caracteres.")
        String nome,

        @PositiveOrZero(message = "A população não pode ser negativa.")
        Long populacao2022,

        @Positive(message = "A área deve ser maior que zero.")
        Double areaKm2) {
}
