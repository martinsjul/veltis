package com.fatec.veltis.dtos;

import com.fatec.veltis.enums.GrauAcademico;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.PositiveOrZero;
import jakarta.validation.constraints.Size;

public record CursoSuperiorRequest(

        @NotNull(message = "O código e-MEC do curso é obrigatório.")
        @Positive(message = "O código e-MEC deve ser positivo.")
        Long codigoEmec,

        @NotBlank(message = "O nome do curso é obrigatório.")
        @Size(max = 150, message = "O nome pode ter no máximo 150 caracteres.")
        String nome,

        GrauAcademico grau,

        @Size(max = 150, message = "A área pode ter no máximo 150 caracteres.")
        String area,

        Boolean gratuito,

        @PositiveOrZero(message = "As vagas não podem ser negativas.")
        Integer vagas,

        @PositiveOrZero(message = "As matrículas não podem ser negativas.")
        Integer matriculas,

        @NotNull(message = "O código da instituição é obrigatório.")
        @Positive(message = "O código da instituição deve ser positivo.")
        Long instituicaoCodigo,

        @NotBlank(message = "O código do município de oferta é obrigatório.")
        @Pattern(regexp = "\\d{7}", message = "O código IBGE do município deve ter 7 dígitos.")
        String municipioCodigo) {
}
