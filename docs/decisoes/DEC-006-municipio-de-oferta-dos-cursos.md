# DEC-006 — Cursos superiores pelo município de oferta

- **Estado:** aceita
- **Data:** 2026-10-19
- **Responsáveis pela decisão:** equipe do projeto
- **Relacionado a:** pipeline `censo_superior`; tabelas `MEC_IES` e `MEC_CURSOS`; DEC-001

## Contexto

No Censo da Educação Superior, a instituição (IES) tem uma **sede**, que pode ficar fora da região, e os cursos têm **locais de oferta**. O arquivo de cursos repete cada curso em "dimensões": 1 = presencial; 2 = EAD por município onde há alunos; 3 = EAD só no total Brasil; 4 = EAD no exterior.

## Alternativas consideradas

- **Filtrar pela sede da IES:** perderia faculdades com campus na RMS e sede em outra cidade (UNIP, PUC-SP, IFSP, UFSCar, Unesp).
- **Filtrar pelo município do curso, dimensões 1 e 2:** mostra o que funciona na cidade (presencial) e onde há alunos de EAD.

## Decisão e justificativa

`MEC_CURSOS` guarda as dimensões 1 e 2 cujo município está na RMS; `MEC_IES` guarda todas as instituições que ofertam nesses municípios, mesmo com sede fora. A chave única inclui a dimensão e o município. As dimensões 3 e 4 não têm município e não entram.

## Consequências e revisão

- Carga de 2024: 115 instituições, 10.381 ofertas (375 presenciais), 33 instituições com curso presencial.
- Um curso EAD aparece em cada município onde tem aluno; para "faculdades que funcionam na cidade", o site usa só o presencial.
- `QT_VAGAS` só existe no presencial (o INEP zera vagas na dimensão 2).
- Revisar quando sair o Censo Superior 2025.
