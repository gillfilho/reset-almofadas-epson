"""
Reset das almofadas (contador de tinta residual) - Epson L1250 / L3250.

Usa como motor de comunicacao o projeto open-source epson_print_conf
(https://github.com/Ircama/epson_print_conf), baixado pelo INSTALAR.bat
para a pasta "motor". A comunicacao e feita pelo cabo USB (IEEE 1284.4 / D4),
porque o firmware dessas impressoras bloqueia a EEPROM pela rede.

Parametros conferidos em duas fontes independentes:
  - ez-reset/devices.xml  (blocos <L12X> = L1250 e <L3250> = L3250)
  - epson_print_conf, perfil "ET-2812" (mesma familia, verificado em hardware)
As duas impressoras usam exatamente os mesmos enderecos e chaves.
"""

import argparse
import copy
import datetime
import logging
import os
import sys
from pathlib import Path

EXE = getattr(sys, "frozen", False)  # True quando empacotado (PyInstaller)
# No .exe os backups ficam ao lado do executavel
PASTA = Path(sys.executable if EXE else __file__).resolve().parent
PASTA_MOTOR = PASTA / "motor"
PASTA_BACKUP = PASTA / "backups"

# ---------------------------------------------------------------------------
# Perfil das impressoras (identico para L1250 e L3250)
# ---------------------------------------------------------------------------
_PERFIL_BASE = {
    "read_key": [74, 54],                  # 0x4A 0x36
    "write_key": b"Maribaya",
    # Contadores (apenas leitura/exibicao)
    "main_waste": {"oids": [48, 49, 47], "divider": 63.46},
    "borderless_waste": {"oids": [50, 51, 47], "divider": 34.16},
    "third_waste": {"oids": [252, 253, 254], "divider": 13.0},
    # Bytes gravados no reset: endereco -> valor
    "raw_waste_reset": {
        48: 0, 49: 0, 47: 0, 52: 0, 53: 0, 54: 94, 50: 0, 51: 0,
        55: 94, 28: 0, 252: 0, 253: 0, 254: 0, 255: 94,
    },
    # Fechamento: limpa o bit 0 do byte 0x100 (sem isso o erro continua)
    "waste_reset_commit": {0x100: 0xFE},
    "serial_number": range(1604, 1614),    # 0x644 .. 0x64D
}

PERFIS = {
    "L1250": dict(_PERFIL_BASE, alias=["L1256", "L1258", "L1259"]),
    "L3250": dict(_PERFIL_BASE, alias=["L3251", "L3253", "L3255",
                                       "L3256", "L3257", "L3258", "L3259"]),
}

NOMES_CONTADORES = {
    "main_waste": "Almofada principal",
    "borderless_waste": "Almofada sem margem (borderless)",
    "third_waste": "Terceira almofada",
}


# ---------------------------------------------------------------------------
# Utilitarios de tela
# ---------------------------------------------------------------------------
def linha():
    print("-" * 60)


def perguntar(texto, opcoes):
    while True:
        resp = input(texto).strip().upper()
        if resp in opcoes:
            return resp
        print("  Opcao invalida. Tente de novo.")


def pausar():
    input("\nPressione ENTER para continuar...")


# ---------------------------------------------------------------------------
# Comunicacao
# ---------------------------------------------------------------------------
def carregar_motor():
    if not EXE:  # no .exe o motor ja vem embutido
        if not (PASTA_MOTOR / "epson_print_conf.py").exists():
            print("ERRO: motor nao encontrado. Execute primeiro o INSTALAR.bat.")
            pausar()
            sys.exit(1)
        sys.path.insert(0, str(PASTA_MOTOR))
    import epson_print_conf as epc
    if not epc.usb_library_available():
        print("ERRO: biblioteca USB ausente. Execute novamente o INSTALAR.bat.")
        pausar()
        sys.exit(1)
    classe = epc.enable_usb_transport()
    return classe


def conectar(classe, modelo, simular, backend=None):
    extra = {}
    if backend:
        extra["backend"] = backend
    # copia: o motor altera o dicionario recebido (expande os "alias")
    return classe(conf_dict=copy.deepcopy(PERFIS), model=modelo,
                  dry_run=simular, **extra)


def ler_niveis(imp):
    """Le os 3 contadores conforme devices.xml (o byte 0x2F e dividido:
    nibble baixo = almofada principal, nibble alto = borderless)."""
    end = [47, 48, 49, 50, 51, 252, 253, 254]
    vals = imp.read_eeprom(end, label="waste_levels")
    if not vals or any(v is None for v in vals):
        print("  Nao foi possivel ler os contadores.")
        return None
    b = dict(zip(end, (int(v, 16) for v in vals)))
    brutos = {
        "main_waste": ((b[47] & 0x0F) << 16) | (b[49] << 8) | b[48],
        "borderless_waste": ((b[47] >> 4) << 16) | (b[51] << 8) | b[50],
        "third_waste": (b[254] << 16) | (b[253] << 8) | b[252],
    }
    niveis = {}
    for chave, bruto in brutos.items():
        niveis[chave] = bruto / imp.parm[chave]["divider"]
        print(f"  {NOMES_CONTADORES[chave]:35s} {niveis[chave]:7.2f} %")
    return niveis


def fazer_backup(imp, modelo):
    """Salva os valores atuais dos bytes que serao alterados."""
    enderecos = list(imp.parm["raw_waste_reset"]) + list(
        imp.parm["waste_reset_commit"])
    valores = imp.read_eeprom(enderecos, label="backup")
    if not valores or any(v is None for v in valores):
        return None
    serial = imp.get_serial_number() or "desconhecido"
    serial = "".join(c for c in serial if c.isalnum()) or "desconhecido"
    PASTA_BACKUP.mkdir(exist_ok=True)
    agora = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    arquivo = PASTA_BACKUP / f"backup_{modelo}_{serial}_{agora}.txt"
    with open(arquivo, "w", encoding="utf-8") as f:
        f.write(f"Modelo: {modelo}\nSerie: {serial}\nData: {agora}\n")
        f.write("Endereco(decimal) = valor(hex) antes do reset\n")
        for end, val in zip(enderecos, valores):
            f.write(f"{end} = {val}\n")
    return arquivo


# ---------------------------------------------------------------------------
# Acoes
# ---------------------------------------------------------------------------
def acao_ver(imp):
    linha()
    print("Nivel das almofadas (aprox.; 100% = limite que trava a impressora)")
    ler_niveis(imp)
    serial = imp.get_serial_number()
    if serial:
        print(f"  Numero de serie: {serial}")


def acao_reset(imp, modelo, simular):
    linha()
    print("Niveis ATUAIS:")
    if ler_niveis(imp) is None and not simular:
        print("Reset cancelado: a impressora nao respondeu a leitura.")
        return
    if not simular:
        arquivo = fazer_backup(imp, modelo)
        if not arquivo:
            print("Reset cancelado: nao foi possivel fazer o backup.")
            return
        print(f"\nBackup salvo em: {arquivo}")
    print("\nATENCAO: o reset apenas zera o contador. Se as almofadas estiverem")
    print("realmente cheias, a tinta pode vazar. Limpe/troque as almofadas ou")
    print("instale um coletor externo.")
    if perguntar("\nConfirmar o reset? (S/N): ", {"S", "N"}) != "S":
        print("Cancelado.")
        return
    relatorio = []
    ok = imp.reset_waste_ink_levels(report=relatorio)
    linha()
    if simular:
        print("SIMULACAO: nenhum byte foi gravado.")
        return
    if ok:
        alterados = sum(1 for r in relatorio if r[3])
        print(f"RESET CONCLUIDO! ({alterados} bytes alterados e conferidos)")
        print("\nNiveis APOS o reset:")
        ler_niveis(imp)
        print("\n>>> DESLIGUE a impressora, aguarde 10 segundos e LIGUE de novo. <<<")
    else:
        print("FALHA no reset. Nada foi confirmado pela impressora.")
        print("Verifique o cabo USB e tente novamente. Detalhes acima.")


def acao_temporario(imp):
    linha()
    print("O reset temporario libera a impressora ATE ELA SER DESLIGADA.")
    print("Nao altera a EEPROM. Util para imprimir algo urgente.")
    if perguntar("Continuar? (S/N): ", {"S", "N"}) != "S":
        return
    if imp.temporary_reset_waste():
        print("Reset temporario aplicado. NAO desligue a impressora.")
    else:
        print("A impressora nao confirmou o reset temporario.")


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Reset almofadas Epson L1250/L3250")
    parser.add_argument("--simular", action="store_true",
                        help="Nao grava nada na impressora (teste)")
    parser.add_argument("--backend", help="Backend USB (avancado: usbprint, libusb, mock)")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.WARNING,
                        format="  [aviso] %(message)s")

    os.system("")  # habilita cores/ANSI no console do Windows
    print("=" * 60)
    print("   RESET DAS ALMOFADAS - EPSON L1250 / L3250  (via USB)")
    print("=" * 60)
    if args.simular:
        print("   *** MODO SIMULACAO: nada sera gravado ***")
    print("\nAntes de continuar:")
    print("  1. Conecte a impressora ao PC pelo CABO USB.")
    print("  2. Ligue a impressora e aguarde ela ficar pronta.")
    print("  3. Conecte UMA impressora por vez.\n")

    classe = carregar_motor()

    print("Qual impressora esta conectada?")
    print("  1 - Epson L1250 (L1256/L1258/L1259)")
    print("  2 - Epson L3250 (L3251/L3253/L3255/L3256/L3258...)")
    modelo = {"1": "L1250", "2": "L3250"}[perguntar("Opcao: ", {"1", "2"})]

    imp = conectar(classe, modelo, args.simular, args.backend)
    try:
        while True:
            linha()
            print(f"Impressora: {modelo}")
            print("  1 - Ver nivel das almofadas")
            print("  2 - RESET das almofadas (permanente)")
            print("  3 - Reset temporario (ate desligar)")
            print("  0 - Sair")
            op = perguntar("Opcao: ", {"0", "1", "2", "3"})
            if op == "0":
                break
            try:
                if op == "1":
                    acao_ver(imp)
                elif op == "2":
                    acao_reset(imp, modelo, args.simular)
                elif op == "3":
                    acao_temporario(imp)
            except TimeoutError as exc:
                print("\nERRO: a impressora nao respondeu pelo USB.")
                print("  - Confira se esta ligada e conectada pelo cabo USB;")
                print("  - Feche outros programas da Epson (monitor de status);")
                print("  - Desconecte e reconecte o cabo.")
                print(f"  Detalhe tecnico: {exc}")
            pausar()
    finally:
        try:
            imp.close()
        except Exception:
            pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nEncerrado.")
