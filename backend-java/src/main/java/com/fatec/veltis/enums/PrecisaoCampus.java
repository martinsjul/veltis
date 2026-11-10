package com.fatec.veltis.enums;

/** Quão exato é o ponto do campus no mapa (levantamento da equipe, DEC-001). */
public enum PrecisaoCampus {

    /** O ponto está no prédio. */
    EDIFICIO,
    /** O ponto está no número do endereço. */
    NUMERO,
    /** Só a rua é certa. */
    RUA;

    /** Texto usado no JSON do mapa ("edificio", "numero", "rua"). */
    public String getValor() {
        return name().toLowerCase();
    }

    public static PrecisaoCampus doValor(String valor) {
        return valueOf(valor.trim().toUpperCase());
    }
}
