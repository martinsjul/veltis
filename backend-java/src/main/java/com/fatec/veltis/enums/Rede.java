package com.fatec.veltis.enums;

/** Rede da instituição de ensino superior. */
public enum Rede {

    PUBLICA("Pública"),
    PRIVADA("Privada");

    private final String rotulo;

    Rede(String rotulo) {
        this.rotulo = rotulo;
    }

    public String getRotulo() {
        return rotulo;
    }

    public static Rede doRotulo(String rotulo) {
        for (Rede r : values()) {
            if (r.rotulo.equalsIgnoreCase(rotulo)) {
                return r;
            }
        }
        throw new IllegalArgumentException("Rede desconhecida: " + rotulo);
    }
}
