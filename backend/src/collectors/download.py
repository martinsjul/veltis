"""Download de arquivos oficiais, com novas tentativas e cache local.

O servidor download.inep.gov.br não envia o certificado intermediário
da cadeia TLS ("RNP ICPEdu GR46 OV TLS CA 2025"). Por isso o requests
falha com "unable to get local issuer certificate". A correção segura
é acrescentar esse intermediário (versionado em backend/certs/) às
autoridades confiáveis padrão (certifi). NUNCA usar verify=False.
"""

from pathlib import Path

import certifi
import requests


BASE_DIR = Path(__file__).resolve().parents[2]

CERT_INTERMEDIARIO_INEP = (
    BASE_DIR / "certs" / "inep_rnp_icpedu_gr46_ov_tls_ca_2025.pem"
)
BUNDLE_GERADO = BASE_DIR / "data" / "processed" / "ca_bundle_inep.pem"

CABECALHOS = {
    "User-Agent": "Veltis-ETL/1.0 (Projeto Integrador Fatec Sorocaba)",
}

TAMANHO_BLOCO = 1024 * 1024


def ca_bundle_inep() -> str:
    """Gera (uma vez) o arquivo de autoridades: certifi + intermediário do INEP."""

    if not BUNDLE_GERADO.exists():
        BUNDLE_GERADO.parent.mkdir(parents=True, exist_ok=True)

        conteudo = (
            Path(certifi.where()).read_text(encoding="utf-8")
            + "\n"
            + CERT_INTERMEDIARIO_INEP.read_text(encoding="utf-8")
        )

        BUNDLE_GERADO.write_text(conteudo, encoding="utf-8")

    return str(BUNDLE_GERADO)


def verificacao_tls(url: str) -> bool | str:
    """Retorna o parâmetro verify adequado para a URL."""

    if "download.inep.gov.br" in url:
        return ca_bundle_inep()

    return True


def baixar_arquivo(
    url: str,
    destino: Path,
    tentativas: int = 3,
    forcar: bool = False,
    timeout: tuple[int, int] = (30, 300),
) -> Path:
    """Baixa url para destino.

    Se o arquivo já existe e forcar=False, reaproveita a cópia local
    (o hash do conteúdo decide depois se precisa recarregar o banco).
    O download vai para um .tmp e só vira o arquivo final se terminar.
    """

    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)

    if destino.exists() and not forcar:
        print(f"Usando arquivo já baixado: {destino.name}")
        return destino

    temporario = destino.with_name(destino.name + ".tmp")

    for tentativa in range(1, tentativas + 1):
        try:
            print(f"Baixando {destino.name} (tentativa {tentativa}/{tentativas})...")

            with requests.get(
                url,
                headers=CABECALHOS,
                stream=True,
                timeout=timeout,
                verify=verificacao_tls(url),
            ) as resposta:
                resposta.raise_for_status()

                with temporario.open("wb") as arquivo:
                    for bloco in resposta.iter_content(chunk_size=TAMANHO_BLOCO):
                        if bloco:
                            arquivo.write(bloco)

            temporario.replace(destino)
            print("Download concluído.")
            return destino

        except requests.RequestException as erro:
            print(f"Falha no download: {erro}")
            temporario.unlink(missing_ok=True)

            if tentativa == tentativas:
                raise RuntimeError(
                    f"Não foi possível baixar {url} após {tentativas} tentativas."
                ) from erro

    raise AssertionError("inalcançável")


def obter_json(url: str, params: dict | None = None, timeout: int = 120):
    """GET simples que devolve o JSON (usado na API do SIDRA)."""

    resposta = requests.get(
        url,
        params=params,
        headers=CABECALHOS,
        timeout=timeout,
        verify=verificacao_tls(url),
    )
    resposta.raise_for_status()
    return resposta.json()
