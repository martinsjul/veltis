package com.fatec.veltis.enums;

/** Grau acadêmico do curso superior (Censo da Educação Superior). */
public enum GrauAcademico {

    BACHARELADO("Bacharelado"),
    LICENCIATURA("Licenciatura"),
    TECNOLOGICO("Tecnológico"),
    BACHARELADO_E_LICENCIATURA("Bacharelado e Licenciatura");

    private final String rotulo;

    GrauAcademico(String rotulo) {
        this.rotulo = rotulo;
    }

    public String getRotulo() {
        return rotulo;
    }

    /** Alguns cursos não informam o grau no Censo: nesse caso devolve null. */
    public static GrauAcademico doRotulo(String rotulo) {
        if (rotulo == null || rotulo.isBlank()) {
            return null;
        }
        for (GrauAcademico g : values()) {
            if (g.rotulo.equalsIgnoreCase(rotulo)) {
                return g;
            }
        }
        throw new IllegalArgumentException("Grau acadêmico desconhecido: " + rotulo);
    }
}
