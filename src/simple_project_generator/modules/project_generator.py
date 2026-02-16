#!/usr/bin/python3

from pathlib import Path
import shutil
import fnmatch
import tempfile
import zipfile
import urllib.request
import os


def extract_zip_to_temp(source: str) -> Path | None:
    """
    Recebe um path local ou uma URL de um arquivo .zip,
    extrai em uma pasta temporária e retorna o Path da pasta extraída.
    
    Retorna None em caso de erro.
    """

    try:
        # Cria diretório temporário persistente
        temp_dir = tempfile.mkdtemp()
        temp_path = Path(temp_dir)

        # Determinar se é URL
        if source.startswith(("http://", "https://")):
            zip_path = temp_path / "downloaded.zip"
            urllib.request.urlretrieve(source, zip_path)
        else:
            zip_path = Path(source)
            if not zip_path.exists():
                return None

        # Validar se é zip válido
        if not zipfile.is_zipfile(zip_path):
            return None

        # Extrair
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(temp_path)

        # Se baixou da internet, remove zip baixado
        if source.startswith(("http://", "https://")):
            zip_path.unlink(missing_ok=True)

        return temp_path

    except Exception:
        return None


def generate_project(
    template_dir: str,
    output_dir: str,
    replacements: dict,
    replace_extensions=None,
    overwrite=False
):
    """
    Gera um novo projeto a partir de um template.

    :param template_dir: Caminho da pasta template
    :param output_dir: Caminho da pasta de saída
    :param replacements: Dict com palavras a substituir
    :param replace_extensions: Lista de padrões tipo ["*.py", "*.md"]
    """

    template_path = Path(template_dir)
    output_path = Path(output_dir)

    if replace_extensions is None:
        replace_extensions = ["*.py", "*.md"]

    if not template_path.exists():
        raise FileNotFoundError("Template directory not found")

    # 🔥 CORREÇÃO DO OVERWRITE
    if output_path.exists():
        if overwrite:
            shutil.rmtree(output_path)
        else:
            raise FileExistsError("Output directory already exists")

    for item in template_path.rglob("*"):

        relative_path = item.relative_to(template_path)

        # Substituir palavras também no nome do arquivo/pasta
        new_relative_str = str(relative_path)
        for key, value in replacements.items():
            new_relative_str = new_relative_str.replace(key, value)

        new_path = output_path / new_relative_str

        if item.is_dir():
            new_path.mkdir(parents=True, exist_ok=True)
            continue

        new_path.parent.mkdir(parents=True, exist_ok=True)

        # Verifica se deve substituir conteúdo
        should_replace = any(
            fnmatch.fnmatch(item.name, pattern)
            for pattern in replace_extensions
        )

        if should_replace:
            content = item.read_text(encoding="utf-8")

            for key, value in replacements.items():
                content = content.replace(key, value)

            new_path.write_text(content, encoding="utf-8")

        else:
            shutil.copy2(item, new_path)

    # 🔥 CORREÇÃO DO RENAME
    old_path = output_path / "src" / "__MODULE_NAME__"
    new_path = output_path / "src" / replacements["{MODULE_NAME}"]

    if old_path.exists():
        if new_path.exists():
            shutil.rmtree(new_path)
        old_path.rename(new_path)

    print(f"Projeto gerado em: {output_path}")


if __name__ == '__main__':

    temp_path = extract_zip_to_temp("/home/fernando/Downloads/codigo/simple_project_generator/pyqt5_project_template_1.zip")
    
    if temp_path:
        try:
            generate_project(
                template_dir=temp_path,
                output_dir="output",
                replacements={
                    "{MODULE_NAME}": "simple_project_generator",
                    "{PROGRAM_NAME}": "simple-project-generator",
                    "{AUTHOR_NAME}": "Fernando Pujaico Rivera",
                    "{AUTHOR_EMAIL}": "fernando.pujaico.rivera@gmail.com",
                    "{SUMMARY}": "my pypi project generator",
                    "{REPOSITORY_PAGE}": "https://github.com/trucomanx",
                    "{REPOSITORY_NAME}": "SimpleProjectGenerator",
                    "{FUNDING_PAGE}": "https://trucomanx.github.io/en/funding.html",
                    "{BUY_ME_A_COFFEE}": "https://ko-fi.com/trucomanx",
                    "{REPOSITORY_RAW_PAGE}": "https://raw.githubusercontent.com/trucomanx",
                },
                replace_extensions=["*.py", "*.md", "*.sh"]
            )
        finally:
            shutil.rmtree(temp_path, ignore_errors=True)


