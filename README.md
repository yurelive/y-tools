# 🧰 y-tools

Ferramentas pessoais em Python, cada uma com um notebook para explorar e testar.

## 📋 Descrição

Cada tool vive em `src/y_tools/<tool>/` como biblioteca reutilizável e tem um
notebook em `notebooks/` que serve de playground. As que fazem sentido também têm
CLI (`python -m y_tools.<tool>`).

| Tool                         | O que faz                                             | Notebook                                  |
| ---------------------------- | ----------------------------------------------------- | ----------------------------------------- |
| [transcricao](#-transcricao) | Transcreve áudio em texto com Whisper, 100% local     | `notebooks/01_transcricao_audio.ipynb`    |

## 🗂️ Estrutura

```text
y-tools/
├── data/                 # entradas (áudios etc.) - fora do git
├── output/               # saídas geradas - fora do git
├── logs/                 # logs das execuções - fora do git
├── notebooks/            # playground: um notebook por tool
│   ├── 00_ambiente.ipynb
│   └── 01_transcricao_audio.ipynb
├── src/y_tools/          # bibliotecas reutilizáveis (import y_tools.*)
│   ├── logger.py         # setup_logger: arquivo + console
│   ├── paths.py          # RAIZ, DATA_DIR, OUTPUT_DIR, LOGS_DIR
│   └── transcricao/
├── tests/
├── environment.yml
└── pyproject.toml
```

## 🚀 Instalação

### Pré-requisitos

- [Miniconda](https://docs.conda.io/en/latest/miniconda.html) (ou Python 3.10+ com `venv`)

Não precisa de ffmpeg: o áudio é decodificado pelo PyAV, que já vem com o
faster-whisper.

### Ambiente

```bash
conda env create -f environment.yml
```

> Se o conda reclamar dos Termos de Serviço dos canais `repo.anaconda.com`, aceite-os
> (`conda tos accept`) ou crie o ambiente só com o conda-forge e instale via pip:
>
> ```bash
> conda create -n y-tools --override-channels -c conda-forge python=3.12 pip -y
> conda activate y-tools
> pip install -e ".[transcricao,notebooks]" -r requirements-dev.txt
> ```

```bash
conda activate y-tools
```

O `environment.yml` instala o pacote em modo editável com os extras de todas as
tools e dos notebooks, mais as ferramentas de desenvolvimento. Para atualizar depois
de mudar dependências:

```bash
conda env update -f environment.yml --prune
```

Ative o filtro que limpa as saídas dos notebooks antes de cada commit (uma vez por clone):

```bash
nbstripout --install --attributes .gitattributes
```

Copie o `.env.example` para `.env` se quiser mudar os padrões:

```bash
cp .env.example .env
```

## 🎙️ Transcrição

Converte áudio (mp3, m4a, wav, ogg/opus do WhatsApp, flac, webm, mp4, aiff...) em
texto usando o [faster-whisper](https://github.com/SYSTRAN/faster-whisper), que roda
o Whisper localmente — nada sai da sua máquina.

### No notebook

Abra `notebooks/01_transcricao_audio.ipynb`, coloque o áudio em `data/` e ajuste a
célula de parâmetros.

### Na linha de comando

```bash
python -m y_tools.transcricao data/reuniao.m4a
```

```bash
python -m y_tools.transcricao data/ --modelo medium --formato srt --formato txt
```

| Opção           | Padrão    | O que faz                                                |
| --------------- | --------- | -------------------------------------------------------- |
| `entrada`       | —         | Arquivo de áudio ou pasta (transcreve todos os áudios)   |
| `-m/--modelo`   | `small`   | `tiny`, `base`, `small`, `medium`, `large-v3`, `turbo`   |
| `-i/--idioma`   | `pt`      | Código do idioma, ou `auto` para detectar                |
| `-f/--formato`  | `txt`     | `txt`, `srt`, `vtt`, `json` — repita para gerar vários   |
| `-o/--saida`    | `output/` | Pasta de saída                                           |
| `-d/--dispositivo` | `auto` | `cpu`, `mps` (GPU do Mac, experimental), `cuda`          |
| `--sem-vad`     | —         | Não pula trechos de silêncio                             |
| `--debug`       | —         | Mostra cada segmento no console                          |

### Em código

```python
from y_tools.transcricao import transcrever_audio, salvar

resultado = transcrever_audio("data/reuniao.m4a", modelo="small", idioma="pt")

print(resultado.texto)
salvar(resultado, formato="srt")  # -> output/reuniao.srt
```

### Qual modelo usar?

| Modelo     | Tamanho | Quando usar                                         |
| ---------- | ------- | --------------------------------------------------- |
| `tiny`     | ~75 MB  | Testes rápidos                                      |
| `base`     | ~145 MB | Áudios curtos e limpos                              |
| `small`    | ~480 MB | Padrão: bom equilíbrio em português                 |
| `medium`   | ~1.5 GB | Áudio com ruído, sotaque ou termos técnicos         |
| `turbo`    | ~1.6 GB | Quase a qualidade do `large-v3`, bem mais rápido    |
| `large-v3` | ~3 GB   | Máxima precisão, mais lento                         |

> ⚠️ O modelo é baixado do Hugging Face na primeira vez que é usado e fica em
> `~/.cache/huggingface`. Depois disso tudo roda offline.

## 🧪 Testes

```bash
pytest
```

```bash
flake8 src tests
```

Os testes não baixam modelos: o Whisper é substituído por um fake.

## 📦 Dependências

- Base: `python-dotenv`
- Extra `transcricao`: `faster-whisper`
- Extra `notebooks`: `ipykernel`, `ipywidgets`, `pandas`
- Desenvolvimento: ver `requirements-dev.txt`

## 🤝 Contribuição

Ver [CONTRIBUTING.md](CONTRIBUTING.md).
