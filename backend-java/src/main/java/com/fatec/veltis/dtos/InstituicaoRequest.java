package com.fatec.veltis.dtos;

import com.fatec.veltis.enums.Rede;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.Size;

public record InstituicaoRequest(

        @NotNull(message = "O código da instituição (co_ies) é obrigatório.")
        @Positive(message = "O código da instituição deve ser positivo.")
        Long codigoIes,

        @NotBlank(message = "O nome é obrigatório.")
        @Size(max = 200, message = "O nome pode ter no máximo 200 caracteres.")
        String nome,

        @Size(max = 30, message = "A sigla pode ter no máximo 30 caracteres.")
        String sigla,

        @NotNull(message = "A rede é obrigatória (PUBLICA ou PRIVADA).")
        Rede rede,

        @Size(max = 50, message = "A organização acadêmica pode ter no máximo 50 caracteres.")
        String organizacaoAcademica) {
}
