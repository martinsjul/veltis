package com.fatec.veltis.dtos;

import com.fatec.veltis.enums.PrecisaoCampus;

import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.Size;

/** JSON de entrada de um campus: as associações vêm pelos códigos (instituição e município). */
public record CampusRequest(

        @NotBlank(message = "O nome do campus é obrigatório.")
        @Size(max = 150, message = "O nome pode ter no máximo 150 caracteres.")
        String nome,

        @NotNull(message = "O código da instituição é obrigatório.")
        @Positive(message = "O código da instituição deve ser positivo.")
        Long instituicaoCodigo,

        @NotBlank(message = "O código do município é obrigatório.")
        @Pattern(regexp = "\\d{7}", message = "O código IBGE do município deve ter 7 dígitos.")
        String municipioCodigo,

        @Size(max = 200, message = "O endereço pode ter no máximo 200 caracteres.")
        String endereco,

        @Size(max = 100, message = "O bairro pode ter no máximo 100 caracteres.")
        String bairro,

        @Pattern(regexp = "\\d{8}", message = "O CEP deve ter 8 dígitos, sem traço.")
        String cep,

        @NotNull(message = "A latitude é obrigatória.")
        @DecimalMin(value = "-25.4", message = "A latitude deve estar dentro do estado de SP (entre -25,4 e -19,7).")
        @DecimalMax(value = "-19.7", message = "A latitude deve estar dentro do estado de SP (entre -25,4 e -19,7).")
        Double latitude,

        @NotNull(message = "A longitude é obrigatória.")
        @DecimalMin(value = "-53.2", message = "A longitude deve estar dentro do estado de SP (entre -53,2 e -44,1).")
        @DecimalMax(value = "-44.1", message = "A longitude deve estar dentro do estado de SP (entre -53,2 e -44,1).")
        Double longitude,

        @NotNull(message = "A precisão é obrigatória (EDIFICIO, NUMERO ou RUA).")
        PrecisaoCampus precisao) {
}
