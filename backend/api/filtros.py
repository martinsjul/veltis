"""Ajudantes para montar o WHERE das consultas com parâmetros seguros.

Os valores do usuário NUNCA entram no texto do SQL: vão sempre como
parâmetros (:nome). Só os trechos fixos escritos aqui viram SQL.
"""

import unicodedata
from dataclasses import dataclass, field
from typing import Any

from fastapi import Query


COM_ACENTO = "áàâãäéèêëíìîïóòôõöúùûüçñ"
SEM_ACENTO = "aaaaaeeeeiiiiooooouuuucn"


def sem_acento_sql(expressao: str) -> str:
    """Expressão SQL que deixa o texto minúsculo e sem acentos."""

    return (
        f"translate(lower({expressao}), "
        f"'{COM_ACENTO}{COM_ACENTO.upper()}', '{SEM_ACENTO}{SEM_ACENTO}')"
    )


def padrao_busca(termo: str) -> str:
    """'São Roque' -> '%sao roque%' (sem acentos, com % e _ escapados)."""

    normalizado = unicodedata.normalize("NFKD", termo.strip().lower())
    sem_acentos = "".join(c for c in normalizado if not unicodedata.combining(c))
    escapado = (
        sem_acentos.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    )
    return f"%{escapado}%"


@dataclass
class Condicoes:
    """Junta as condições do WHERE e os parâmetros correspondentes."""

    partes: list[str] = field(default_factory=list)
    params: dict[str, Any] = field(default_factory=dict)

    def adicionar(self, condicao: str, **params: Any) -> None:
        self.partes.append(condicao)
        self.params.update(params)

    def busca(self, colunas: list[str], termo: str | None, nome: str = "busca") -> None:
        if not termo:
            return
        alternativas = " OR ".join(f"{sem_acento_sql(c)} LIKE :{nome}" for c in colunas)
        self.adicionar(f"({alternativas})", **{nome: padrao_busca(termo)})

    @property
    def where(self) -> str:
        return ("WHERE " + " AND ".join(self.partes)) if self.partes else ""


@dataclass
class Paginacao:
    pagina: int
    por_pagina: int

    @property
    def params(self) -> dict[str, int]:
        return {"limite": self.por_pagina, "deslocamento": (self.pagina - 1) * self.por_pagina}


def paginacao(
    pagina: int = Query(1, ge=1, description="Número da página, começando em 1."),
    por_pagina: int = Query(50, ge=1, le=500, description="Itens por página (máximo 500)."),
) -> Paginacao:
    return Paginacao(pagina=pagina, por_pagina=por_pagina)


def pagina_de(itens: list[dict], pag: Paginacao) -> dict:
    """Monta a resposta paginada. As consultas trazem o total em _total."""

    total = itens[0].pop("_total") if itens else 0
    for item in itens[1:]:
        item.pop("_total", None)
    return {"total": total, "pagina": pag.pagina, "por_pagina": pag.por_pagina, "itens": itens}


PADRAO_MUNICIPIO = r"^\d{7}$"
DESCRICAO_MUNICIPIO = "Código IBGE do município, com 7 dígitos (ex.: 3552205 = Sorocaba)."
DESCRICAO_ANO = "Ano do Censo. Se não for informado, usa o mais recente carregado."
DESCRICAO_BUSCA = "Trecho do nome, sem diferenciar maiúsculas nem acentos."
