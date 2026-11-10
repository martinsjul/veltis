package com.fatec.veltis.enums;

/** Rede (dependência administrativa) da escola, como no Censo Escolar do INEP. */
public enum Dependencia {

    FEDERAL("Federal"),
    ESTADUAL("Estadual"),
    MUNICIPAL("Municipal"),
    PRIVADA("Privada");

    private final String rotulo;

    Dependencia(String rotulo) {
        this.rotulo = rotulo;
    }

    public String getRotulo() {
        return rotulo;
    }

    /** Converte o texto do arquivo oficial ("Estadual") para o enum. */
    public static Dependencia doRotulo(String rotulo) {
        for (Dependencia d : values()) {
            if (d.rotulo.equalsIgnoreCase(rotulo)) {
                return d;
            }
        }
        throw new IllegalArgumentException("Dependência desconhecida: " + rotulo);
    }
}
