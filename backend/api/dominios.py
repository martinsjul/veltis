"""Valores aceitos nos filtros e o texto que cada um representa.

Os mesmos textos aparecem nas views (ds_dependencia, ds_modalidade...).
"""

from enum import Enum, StrEnum


class Dependencia(StrEnum):
    federal = "federal"
    estadual = "estadual"
    municipal = "municipal"
    privada = "privada"


class Modalidade(StrEnum):
    presencial = "presencial"
    ead = "ead"


class Grau(StrEnum):
    bacharelado = "bacharelado"
    licenciatura = "licenciatura"
    tecnologico = "tecnologico"
    bacharelado_e_licenciatura = "bacharelado_e_licenciatura"


class Rede(StrEnum):
    publica = "publica"
    privada = "privada"


class Detalhe(StrEnum):
    simples = "simples"
    completo = "completo"


CODIGO_DEPENDENCIA = {
    Dependencia.federal: 1,
    Dependencia.estadual: 2,
    Dependencia.municipal: 3,
    Dependencia.privada: 4,
}

ROTULOS = {
    Dependencia.federal: "Federal",
    Dependencia.estadual: "Estadual",
    Dependencia.municipal: "Municipal",
    Dependencia.privada: "Privada",
    Modalidade.presencial: "Presencial",
    Modalidade.ead: "EAD",
    Grau.bacharelado: "Bacharelado",
    Grau.licenciatura: "Licenciatura",
    Grau.tecnologico: "Tecnológico",
    Grau.bacharelado_e_licenciatura: "Bacharelado e Licenciatura",
    Rede.publica: "Pública",
    Rede.privada: "Privada",
}


def opcoes(enum: type[Enum]) -> list[dict[str, str]]:
    return [{"valor": item.value, "rotulo": ROTULOS[item]} for item in enum]
