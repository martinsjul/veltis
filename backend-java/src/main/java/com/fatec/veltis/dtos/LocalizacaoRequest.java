package com.fatec.veltis.dtos;

import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

/**
 * Ponto da escola no mapa. Os limites de latitude e longitude são os do
 * estado de São Paulo: um ponto fora deles é erro de digitação (ex.: trocar
 * latitude com longitude).
 */
public record LocalizacaoRequest(

        @NotNull(message = "A latitude é obrigatória.")
        @DecimalMin(value = "-25.4", message = "A latitude deve estar dentro do estado de SP (entre -25,4 e -19,7).")
        @DecimalMax(value = "-19.7", message = "A latitude deve estar dentro do estado de SP (entre -25,4 e -19,7).")
        Double latitude,

        @NotNull(message = "A longitude é obrigatória.")
        @DecimalMin(value = "-53.2", message = "A longitude deve estar dentro do estado de SP (entre -53,2 e -44,1).")
        @DecimalMax(value = "-44.1", message = "A longitude deve estar dentro do estado de SP (entre -53,2 e -44,1).")
        Double longitude,

        @NotBlank(message = "Informe a fonte do ponto (ex.: INEP - Catálogo de Escolas).")
        @Size(max = 120, message = "A fonte pode ter no máximo 120 caracteres.")
        String fonte,

        @NotBlank(message = "Informe a precisão do ponto.")
        @Pattern(regexp = "oficial|numero|numero_aproximado|logradouro",
                 message = "A precisão deve ser oficial, numero, numero_aproximado ou logradouro.")
        String precisao) {
}
