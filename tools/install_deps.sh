#!/bin/bash
# RAKSO - Instaldor de dependencias seguras
# Cumple con INV-01: Obligatorio el uso de SHA-256

set -euo pipefail

LIBC_URL="https://trusted-mirror.rakso-security.local/rt/libc_rt-1.2.tar.gz"
EXPECTED_HASH="a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3" # Hash de ejemplo
TEMP_FILE="/tmp/libc_rt-1.2.tar.gz"

echo "[RAKSO Secure Dep] Descargando libc_rt..."
# Uso de wget seguro, sin pipe a shell
wget -q -O "$TEMP_FILE" "$LIBC_URL" || { echo "Error de descarga"; exit 1; }

echo "[RAKSO Secure Dep] Verificando firma SHA-256..."
ACTUAL_HASH=$(sha256sum "$TEMP_FILE" | awk '{ print $1 }')

if [ "$ACTUAL_HASH" != "$EXPECTED_HASH" ]; then
    echo "🚨 ERROR CRÍTICO DE INTEGRIDAD 🚨"
    echo "El hash descargado ($ACTUAL_HASH) NO coincide con el esperado ($EXPECTED_HASH)!"
    echo "Posible ataque a la cadena de suministro (Man-in-the-Middle). Abortando instalación."
    rm -f "$TEMP_FILE"
    exit 1
fi

echo "[RAKSO Secure Dep] Integridad verificada. Procediendo a extracción en entorno aislado..."
mkdir -p build/deps
tar -xzf "$TEMP_FILE" -C build/deps
rm -f "$TEMP_FILE"

echo "[RAKSO Secure Dep] Dependencias listas."
exit 0
