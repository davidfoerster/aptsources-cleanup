APPLICATION_NAME = aptsources-cleanup
BUILD_DIR = dist

SRC_DIR = src
PO_DIR = po
LOCALES_DIR = share/locales
LOCALES_DOMAIN = messages

ZIP = zip -9
GETTEXT = xgettext -F -L Python -k_ -k_U -k_N:1,2 \
	--package-name=$(APPLICATION_NAME) --package-version=0.1 \
	--copyright-holder='David P. W. Forster' \
	--msgid-bugs-address=https://github.com/davidfoerster/aptsources-cleanup/issues
MSGFMT = msgfmt
MSGMERGE = msgmerge -F
PYTHON = python3 -s

rwildcard = $(foreach d,$(wildcard $(1)*),$(call rwildcard,$(d)/,$(2)) $(filter $(subst *,%,$(2)),$(d)))
dirname = $(patsubst %/,%,$(dir $(1)))
has_msgtools = 1
# has_msgtools = $(shell for c in $(firstword $(GETTEXT)) $(firstword $(MSGFMT)) $(firstword $(MSGMERGE)); do command -v -- "$$c" || { printf "Warning: \"%s\" is unavailable. Cannot generate translation data.\n\n" "$$c" >&2; exit 1; }; done > /dev/null && echo 1)

SOURCES = $(call rwildcard,$(SRC_DIR),*.py)

MESSAGES_PO = $(shell find $(PO_DIR) -mindepth 1 -name '*.po')
MESSAGES_MO = $(patsubst $(PO_DIR)/%.po,$(LOCALES_DIR)/%.mo,$(MESSAGES_PO))
MESSAGES_POT = $(PO_DIR)/$(LOCALES_DOMAIN).pot
MESSAGES_SYMLINKS = $(notdir $(call dirname,$(call dirname,$(filter-out $(MESSAGES_PO), $(wildcard $(PO_DIR)/*/LC_MESSAGES/*.po)))))

DIST_FILES = $(addprefix $(ZIP_TARGET_PKG)/,$(patsubst $(SRC_DIR)/%,%,$(SOURCES)) $(MESSAGES_MO) $(addprefix $(LOCALES_DIR)/,$(MESSAGES_SYMLINKS)) README.md)

ZIP_TARGET = $(BUILD_DIR)/$(APPLICATION_NAME).zip
ZIP_TARGET_PKG = $(basename $(ZIP_TARGET)).pkg


zip: $(ZIP_TARGET)


dist: $(DIST_FILES)


clean:
	rm -f -- $(ZIP_TARGET) $(MESSAGES_POT) $(wildcard $(LOCALES_DIR)/*/LC_MESSAGES/*.mo) $(DIST_FILES)


messages_template: $(MESSAGES_POT)

$(PO_DIR)/%.pot: $(SOURCES) $(shell $(PYTHON) tools/get_module_file.py argparse) | $(LOCALES_DIR)/
	$(GETTEXT) -d $(basename $(notdir $@)) -o $@ -- $^


messages_update: $(MESSAGES_PO)

%.po: $(MESSAGES_POT)
	$(MSGMERGE) -U -- $@ $<


messages: $(MESSAGES_MO) $(addprefix $(LOCALES_DIR)/,$(MESSAGES_SYMLINKS))


$(sort $(LOCALES_DIR)/ $(ZIP_TARGET_PKG)/ $(dir $(MESSAGES_MO) $(ZIP_TARGET) $(DIST_FILES))):
	mkdir -p -- $@


.PHONY: zip clean dist messages messages_template messages_update

.SECONDEXPANSION:


DIST_CP_CMP = cp -PT -- $< $@

$(ZIP_TARGET_PKG)/%.py: $(SRC_DIR)/%.py | $$(@D)/
	$(DIST_CP_CMP)

$(ZIP_TARGET_PKG)/%: % | $$(@D)/
	$(DIST_CP_CMP)

$(addprefix $(LOCALES_DIR)/,$(MESSAGES_SYMLINKS)): $$(patsubst $$(LOCALES_DIR)/%,$$(PO_DIR)/%,$$@) | $$(@D)/
	$(DIST_CP_CMP)


$(ZIP_TARGET): $(DIST_FILES) | $$(@D)/
	cd $(ZIP_TARGET_PKG) && exec $(ZIP) -FS --symlinks $(abspath $@) -- $(patsubst $(ZIP_TARGET_PKG)/%,%,$^)


$(LOCALES_DIR)/%.mo: $(PO_DIR)/%.po | $$(@D)/
	$(MSGFMT) -o $@ -- $<
