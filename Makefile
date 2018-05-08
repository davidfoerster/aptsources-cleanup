APPLICATION_NAME = aptsources-cleanup
BUILD_DIR = build
SRC_DIR = src
LOCALES_DIR = $(SRC_DIR)/locales
LOCALES_DOMAIN = messages
ZIP = zip -9
GETTEXT = xgettext -F -L Python -k_ -k_U -k_N:1,2 \
	--package-name=$(APPLICATION_NAME) --package-version=0.1 \
	--copyright-holder='David P. W. Forster' \
	--msgid-bugs-address=https://github.com/davidfoerster/aptsources-cleanup/issues
MSGFMT = msgfmt
MSGMERGE = msgmerge -F
PYTHON = python3 -s

rwildcard = $(foreach d,$(wildcard $1*),$(call rwildcard,$d/,$2) $(filter $(subst *,%,$2),$d))
dirname = $(patsubst %/,%,$(dir $(1)))
pymodule_path = $(shell $(PYTHON) -c 'from __future__ import absolute_import, print_function; import sys, importlib, operator; print(*map(operator.attrgetter("__file__"), map(importlib.import_module, sys.argv[1:])), sep="\n")' $(1))
has_msgtools = 1 #$(shell for c in $(firstword $(GETTEXT)) $(firstword $(MSGFMT)) $(firstword $(MSGMERGE)); do command -v -- "$$c" || { printf "Warning: \"%s\" is unavailable. Cannot generate translation data.\n\n" "$$c" >&2; exit 1; }; done > /dev/null && echo 1)

SOURCES = $(call rwildcard, $(SRC_DIR), *.py)
ZIP_TARGET = $(BUILD_DIR)/$(APPLICATION_NAME).zip
MESSAGES_PO = $(shell find $(LOCALES_DIR) -mindepth 1 -name '*.po')
MESSAGES_MO = $(patsubst %.po,%.mo,$(MESSAGES_PO))
MESSAGES_POT = $(LOCALES_DIR)/$(LOCALES_DOMAIN).pot
MESSAGES_SYMLINKS = $(call dirname,$(call dirname,$(filter-out $(MESSAGES_MO), $(wildcard $(LOCALES_DIR)/*/LC_MESSAGES/*.mo))))


zip: $(ZIP_TARGET)

clean:
	rm -f -- $(ZIP_TARGET) $(MESSAGES_POT) $(wildcard $(LOCALES_DIR)/*/LC_MESSAGES/*.mo)


$(ZIP_TARGET): $(SOURCES) README.md | $(BUILD_DIR)
$(ZIP_TARGET): $(if $(has_msgtools),$(MESSAGES_MO) $(MESSAGES_SYMLINKS),)
	cd $(SRC_DIR) && exec $(ZIP) --symlinks $(abspath $@) -- $(patsubst $(SRC_DIR)/%,%,$(filter $(SRC_DIR)/%,$^))
	$(ZIP) $(abspath $@) -- $(filter-out $(SRC_DIR)/%,$^)


messages_template: $(MESSAGES_POT)

$(LOCALES_DIR)/%.pot: $(SOURCES) $(call pymodule_path,argparse) | $(LOCALES_DIR)
	cd $(SRC_DIR) && exec $(GETTEXT) -d $(basename $(notdir $@)) -o $(patsubst $(SRC_DIR)/%,%,$@ -- $^)


messages_update: $(MESSAGES_POT) $(MESSAGES_PO)

%.po: $(MESSAGES_POT)
	$(MSGMERGE) -U -- $@ $<


messages: $(MESSAGES_MO)

%.mo: %.po
	$(MSGFMT) -o $@ -- $<


$(BUILD_DIR) $(LOCALES_DIR):
	mkdir -p -- $@


.PHONY: zip clean messages messages_template messages_update
