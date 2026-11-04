"""Formatação de valores para a CLI."""


def human_bytes(value: int) -> str:
    """Converte bytes para uma unidade legível, com uma casa decimal."""
    tamanho = float(value)
    for unidade in ("B", "KB", "MB", "GB", "TB"):
        if tamanho < 1024 or unidade == "TB":
            if unidade == "B":
                return f"{tamanho:.0f} B"
            return f"{tamanho:.1f} {unidade}"
        tamanho /= 1024
    return f"{tamanho:.1f} TB"
