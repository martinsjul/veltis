"""Controle de ingestão: fontes, hash e registro de cada carga.

Antes, cada coletor tinha a sua própria cópia destas funções.
Agora todos usam o mesmo fluxo:

    with carga(FONTE, periodo=..., versao=..., arquivo=..., hash_arquivo=...) as ing:
        if ing is None:
            return                      # esta versão já foi carregada
        ... grava os dados usando ing.conexao e ing.id_ingestao ...
        ing.registrar_contagens(lidos=..., carregados=...)

O registro em CONTROLE_INGESTAO passa por INICIADA e termina em
CONCLUIDA (na mesma transação dos dados) ou FALHA (numa transação
separada, para o erro ficar gravado mesmo com o rollback dos dados).
"""

import hashlib
import json
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

from sqlalchemy import text

from src.database import get_engine


@dataclass(frozen=True)
class Fonte:
    orgao: str
    nome: str
    url_oficial: str
    periodicidade: str
    tipo: str = "OFICIAL_PRINCIPAL"
    observacao: str | None = None


# ------------------------------------------------------------
# Hash
# ------------------------------------------------------------

def hash_arquivo(caminho: Path) -> str:
    sha256 = hashlib.sha256()

    with Path(caminho).open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            sha256.update(bloco)

    return sha256.hexdigest()


def hash_json(dados) -> str:
    conteudo = json.dumps(dados, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(conteudo).hexdigest()


# ------------------------------------------------------------
# Fonte de dados
# ------------------------------------------------------------

def obter_id_fonte(conexao, fonte: Fonte) -> int:
    """Cadastra a fonte se não existir e devolve o seu id."""

    return conexao.execute(
        text(
            """
            INSERT INTO fonte_dados (
                no_orgao, no_fonte, ds_url_oficial,
                ds_periodicidade, ds_tipo_fonte, ds_observacao
            )
            VALUES (:orgao, :nome, :url, :periodicidade, :tipo, :observacao)
            ON CONFLICT (no_orgao, no_fonte) DO UPDATE SET
                ds_url_oficial = EXCLUDED.ds_url_oficial,
                ds_periodicidade = EXCLUDED.ds_periodicidade,
                ds_tipo_fonte = EXCLUDED.ds_tipo_fonte,
                ds_observacao = COALESCE(EXCLUDED.ds_observacao, fonte_dados.ds_observacao)
            RETURNING id_fonte
            """
        ),
        {
            "orgao": fonte.orgao,
            "nome": fonte.nome,
            "url": fonte.url_oficial,
            "periodicidade": fonte.periodicidade,
            "tipo": fonte.tipo,
            "observacao": fonte.observacao,
        },
    ).scalar_one()


def ja_processado(conexao, id_fonte: int, hash_: str, arquivo: str) -> bool:
    """True se este arquivo, com este conteúdo, já foi carregado com sucesso."""

    return conexao.execute(
        text(
            """
            SELECT 1
            FROM controle_ingestao
            WHERE id_fonte = :id_fonte
              AND ds_hash_sha256 = :hash
              AND no_arquivo_origem = :arquivo
              AND ds_status = 'CONCLUIDA'
            LIMIT 1
            """
        ),
        {"id_fonte": id_fonte, "hash": hash_, "arquivo": arquivo},
    ).first() is not None


# ------------------------------------------------------------
# Registro de uma carga
# ------------------------------------------------------------

@dataclass
class Ingestao:
    fonte: Fonte
    periodo: str
    versao: str
    arquivo: str
    hash_: str
    dt_obtencao: date | None = None
    id_fonte: int | None = None
    id_ingestao: int | None = None
    conexao: object | None = None
    lidos: int | None = None
    carregados: int | None = None
    rejeitados: int = 0
    observacoes: list[str] = field(default_factory=list)

    def registrar_contagens(
        self,
        lidos: int,
        carregados: int,
        rejeitados: int = 0,
        observacao: str | None = None,
    ) -> None:
        self.lidos = lidos
        self.carregados = carregados
        self.rejeitados = rejeitados

        if observacao:
            self.observacoes.append(observacao)


def _iniciar(ing: Ingestao, forcar: bool) -> bool:
    with get_engine().begin() as conexao:
        ing.id_fonte = obter_id_fonte(conexao, ing.fonte)

        if not forcar and ja_processado(conexao, ing.id_fonte, ing.hash_, ing.arquivo):
            return False

        ing.id_ingestao = conexao.execute(
            text(
                """
                INSERT INTO controle_ingestao (
                    id_fonte, co_periodo_referencia, ds_versao, no_arquivo_origem,
                    dt_obtencao, dt_processamento, ds_hash_sha256, ds_status
                )
                VALUES (
                    :id_fonte, :periodo, :versao, :arquivo,
                    :obtencao, :agora, :hash, 'INICIADA'
                )
                RETURNING id_ingestao
                """
            ),
            {
                "id_fonte": ing.id_fonte,
                "periodo": ing.periodo,
                "versao": ing.versao,
                "arquivo": ing.arquivo,
                "obtencao": ing.dt_obtencao or date.today(),
                "agora": datetime.now(),
                "hash": ing.hash_,
            },
        ).scalar_one()

    return True


def _concluir(ing: Ingestao) -> None:
    if ing.carregados is None:
        raise RuntimeError(
            "O coletor terminou sem chamar registrar_contagens(); "
            "a carga não foi confirmada."
        )

    ing.conexao.execute(
        text(
            """
            UPDATE controle_ingestao SET
                ds_status = 'CONCLUIDA',
                dt_processamento = :agora,
                qt_registros_lidos = :lidos,
                qt_registros_carregados = :carregados,
                qt_registros_rejeitados = :rejeitados,
                ds_observacao = :observacao
            WHERE id_ingestao = :id
            """
        ),
        {
            "agora": datetime.now(),
            "lidos": ing.lidos,
            "carregados": ing.carregados,
            "rejeitados": ing.rejeitados,
            "observacao": " ".join(ing.observacoes) or None,
            "id": ing.id_ingestao,
        },
    )


def _falhar(ing: Ingestao, erro: BaseException) -> None:
    mensagem = f"{type(erro).__name__}: {erro}"[:2000]

    with get_engine().begin() as conexao:
        conexao.execute(
            text(
                """
                UPDATE controle_ingestao SET
                    ds_status = 'FALHA',
                    dt_processamento = :agora,
                    ds_observacao = :mensagem
                WHERE id_ingestao = :id
                """
            ),
            {"agora": datetime.now(), "mensagem": mensagem, "id": ing.id_ingestao},
        )


@contextmanager
def carga(
    fonte: Fonte,
    *,
    periodo: str,
    versao: str,
    arquivo: str,
    hash_arquivo: str,
    forcar: bool = False,
    dt_obtencao: date | None = None,
):
    """Abre uma carga controlada. Entrega None se já foi processada."""

    ing = Ingestao(
        fonte=fonte,
        periodo=str(periodo),
        versao=versao,
        arquivo=arquivo,
        hash_=hash_arquivo,
        dt_obtencao=dt_obtencao,
    )

    if not _iniciar(ing, forcar):
        print(f"{arquivo}: esta versão já foi carregada. Nada a fazer.")
        yield None
        return

    try:
        with get_engine().begin() as conexao:
            ing.conexao = conexao
            yield ing
            _concluir(ing)
    except BaseException as erro:
        _falhar(ing, erro)
        raise

    print(
        f"{arquivo}: carga {ing.id_ingestao} CONCLUIDA "
        f"({ing.carregados} registros carregados)."
    )
