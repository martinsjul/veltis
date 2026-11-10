package com.fatec.veltis.enums;

/** Situação de funcionamento da escola no Censo Escolar. */
public enum SituacaoFuncionamento {

    EM_ATIVIDADE("Em atividade"),
    PARALISADA("Paralisada"),
    EXTINTA("Extinta no ano");

    private final String rotulo;

    SituacaoFuncionamento(String rotulo) {
        this.rotulo = rotulo;
    }

    public String getRotulo() {
        return rotulo;
    }

    public static SituacaoFuncionamento doRotulo(String rotulo) {
        for (SituacaoFuncionamento s : values()) {
            if (s.rotulo.equalsIgnoreCase(rotulo)) {
                return s;
            }
        }
        throw new IllegalArgumentException("Situação desconhecida: " + rotulo);
    }
}
