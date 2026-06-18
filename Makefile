# RAKSO FORTRESS OS - Makefile
# Cumple con RAKSO_SPEC_PHASE_1 (Invariantes INV-01, INV-02)

CC = gcc
CFLAGS = -Wall -Wextra -Werror -O2 -fstack-protector-strong -D_FORTIFY_SOURCE=2
LDFLAGS = -Wl,-z,relro,-z,now

DESTDIR ?= /
PREFIX ?= usr/local

.PHONY: all clean install deps

all: 
	@echo "Construyendo RAKSO OS..."
	# (Compilación del kernel iría aquí)

deps:
	@echo "Verificando dependencias con SHA-256..."
	bash tools/install_deps.sh

install: all
	@echo "Instalando utilidades del sistema..."
	install -d $(DESTDIR)$(PREFIX)/bin
	# NOTA DE SEGURIDAD (INV-02): La instalación se hace explícitamente con 0755. 
	# Queda TERMINANTEMENTE PROHIBIDO usar chmod u+s (SUID).
	# Si existe `rakso_debugsh`, solo se instalará sin SUID.
	@if [ -f "utils/rakso_debugsh" ]; then \
		install -m 0755 utils/rakso_debugsh $(DESTDIR)$(PREFIX)/bin/ ; \
	fi

clean:
	@echo "Limpiando binarios..."
	rm -rf build/
