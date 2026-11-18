# Reset das almofadas – Epson L1250 / L3250

Programa simples, em português, para zerar o contador de tinta residual (as “almofadas”) das impressoras **Epson EcoTank L1250** e **L3250**, inclusive as variantes L1256/L1258/L1259 e L3251/L3253/L3255/L3256/L3257/L3258/L3259.

> ⚠️ O reset só zera o **contador**. Se as almofadas estiverem realmente cheias, a tinta pode vazar. Limpe ou troque as almofadas, ou instale um coletor externo.

## Uso rápido (sem instalar nada)

1. Baixe o `ResetAlmofadasEpson.exe` na página de [Releases](../../releases).
2. Conecte a impressora pelo **cabo USB** (uma por vez), ligue-a e aguarde ela ficar pronta.
3. Abra o `.exe`, escolha o modelo e use a opção **2 – RESET**.
4. Desligue a impressora, aguarde 10 segundos e ligue de novo.

O computador precisa ter o driver normal da Epson instalado, o mesmo usado para imprimir.

Para testar sem gravar nada, rode `ResetAlmofadasEpson.exe --simular`.

## Opções do menu

| Opção | O que faz |
|---|---|
| 1 | Mostra o nível atual das almofadas |
| 2 | Reset permanente (grava a EEPROM) |
| 3 | Reset temporário: libera a impressora até ela ser desligada, sem gravar nada |

## Por que só pelo USB?

O firmware dessas impressoras bloqueia o acesso à EEPROM pela rede (Wi-Fi/SNMP). Pelo cabo USB (protocolo IEEE 1284.4 / D4), os mesmos comandos funcionam.

## Segurança

- Antes de gravar, o programa **pergunta o modelo à própria impressora**. Se não for L1250/L3250 (ou uma variante), se for diferente do modelo escolhido no menu ou se a impressora não informar o modelo, o reset é **bloqueado** e nada é gravado. Outro modelo tem outro mapa de memória e poderia ser danificado.
- Durante a gravação (poucos segundos), Ctrl+C é ignorado e o programa avisa para não desligar a impressora nem desconectar o cabo.
- Antes de cada reset, os valores originais são salvos na pasta `backups`, ao lado do programa.
- Cada byte gravado é **relido e conferido**. Se a impressora responder “OK” sem gravar, o programa mostra falha.
- Se a primeira leitura ou o backup falharem, o reset é cancelado antes de gravar qualquer coisa.

## Parâmetros usados

A L1250 e a L3250 usam parâmetros idênticos, conferidos em duas fontes independentes: os blocos `<L12X>` e `<L3250>` do [`devices.xml` do ez-reset](https://github.com/CiRIP/ez-reset) e o perfil ET-2812 (mesma família, verificado em hardware) do [epson_print_conf](https://github.com/Ircama/epson_print_conf).

- Chave de leitura: `0x4A 0x36`
- Bytes zerados: `0x1C, 0x2F–0x35, 0xFC–0xFE`; bytes `0x36, 0x37, 0xFF` = `0x5E`
- Fechamento: limpa o bit 0 do byte `0x100` (sem isso, o erro de almofada continua)

## Rodar a partir do código-fonte

1. Execute `INSTALAR.bat`. Ele instala o Python 3.12 via `winget` se necessário, baixa o motor `epson_print_conf` (numa versão fixa) e as dependências.
2. Execute `RESETAR.bat`.
3. (Opcional) `GERAR_EXE.bat` gera `dist\ResetAlmofadasEpson.exe`.

## Créditos e licença

A comunicação com a impressora é feita pelo [epson_print_conf](https://github.com/Ircama/epson_print_conf), de Ircama (EUPL-1.2), usado no commit `2dc3beb`. O executável embute esse código.

Este projeto é distribuído sob a licença **EUPL-1.2** (veja [LICENSE](LICENSE)). Use por sua conta e risco.
