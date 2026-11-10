package com.fatec.veltis.dtos;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.Size;

public record CursoTecnicoRequest(

        @NotNull(message = "O código do curso é obrigatório.")
        @Positive(message = "O código do curso deve ser positivo.")
        Long codigo,

        @NotBlank(message = "O nome é obrigatório.")
        @Size(max = 150, message = "O nome pode ter no máximo 150 caracteres.")
        String nome,

        @Size(max = 150, message = "A área pode ter no máximo 150 caracteres.")
        String area) {
}
