package com.fatec.veltis.dtos;

import com.fatec.veltis.enums.Dependencia;
import com.fatec.veltis.enums.SituacaoFuncionamento;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.Size;

/**
 * JSON de entrada de uma escola. O município vem só pelo código (municipioCodigo):
 * o service busca o Municipio e faz a associação.
 */
public record EscolaRequest(

        @NotNull(message = "O código INEP é obrigatório.")
        @Positive(message = "O código INEP deve ser positivo.")
        Long codigoInep,

        @NotBlank(message = "O nome é obrigatório.")
        @Size(max = 150, message = "O nome pode ter no máximo 150 caracteres.")
        String nome,

        @NotBlank(message = "O código do município é obrigatório.")
        @Pattern(regexp = "\\d{7}", message = "O código IBGE do município deve ter 7 dígitos.")
        String municipioCodigo,

        @NotNull(message = "A dependência é obrigatória (FEDERAL, ESTADUAL, MUNICIPAL ou PRIVADA).")
        Dependencia dependencia,

        @NotNull(message = "A situação é obrigatória (EM_ATIVIDADE, PARALISADA ou EXTINTA).")
        SituacaoFuncionamento situacao,

        @Size(max = 200, message = "O endereço pode ter no máximo 200 caracteres.")
        String endereco,

        @Pattern(regexp = "\\d{8}", message = "O CEP deve ter 8 dígitos, sem traço.")
        String cep,

        @Size(max = 20, message = "O telefone pode ter no máximo 20 caracteres.")
        String telefone,

        @NotNull(message = "Informe se a escola oferece ensino médio (true ou false).")
        Boolean ofereceEnsinoMedio) {
}
