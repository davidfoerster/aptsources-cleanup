APPLICATION_NAME = aptsources-cleanup
APPLICATION_VERSION = $(shell head -n 1 VERSION)
BUILD_DIR = dist
SRC_DIR = src
PO_DIR = po
LOCALES_DIR = share/locales
LOCALES_DOMAIN = messages

ZIP = zip -9
GETTEXT = xgettext -F -L Python -k_ -k_U -k_N:1,2 \
	--package-name="$(APPLICATION_NAME)" \
	--package-version="$(APPLICATION_VERSION)" \
	--copyright-holder='David P. W. Forster' \
	--msgid-bugs-address=https://github.com/davidfoerster/aptsources-cleanup/issues
MSGFMT = msgfmt
MSGMERGE = msgmerge -F --backup=none
PYTHON = python3 -s
GPG = $(shell command -v gpg2 || { gpg --version | grep -qe '^gpg.*[ v]2\.[0-9]' && echo gpg; })

rwildcard = $(foreach d,$(wildcard $(1)*),$(call rwildcard,$(d)/,$(2)) $(filter $(subst *,%,$(2)),$(d)))
dirname = $(patsubst %/,%,$(dir $(1)))
has_msgtools = 1
# has_msgtools = $(shell for c in $(firstword $(GETTEXT)) $(firstword $(MSGFMT)) $(firstword $(MSGMERGE)); do command -v -- "$$c" || { printf "Warning: \"%s\" is unavailable. Cannot generate translation data.\n\n" "$$c" >&2; exit 1; }; done > /dev/null && echo 1)

VERSION_DATA = aptsources_cleanup/util/version/_data.py
SOURCES = $(filter-out $(SRC_DIR)/$(VERSION_DATA),$(call rwildcard,$(SRC_DIR),*.py))

MESSAGES_PO = $(shell find $(PO_DIR) -mindepth 1 -name '*.po')
MESSAGES_MO = $(patsubst $(PO_DIR)/%.po,$(LOCALES_DIR)/%.mo,$(MESSAGES_PO))
MESSAGES_POT = $(PO_DIR)/$(LOCALES_DOMAIN).pot
MESSAGES_SYMLINKS = $(notdir $(call dirname,$(call dirname,$(filter-out $(MESSAGES_PO), $(wildcard $(PO_DIR)/*/LC_MESSAGES/*.po)))))

ZIP_TARGET = $(BUILD_DIR)/$(APPLICATION_NAME).pyz
ZIP_TARGET_PKG = $(basename $(ZIP_TARGET)).pkg
CHECKSUMMED_FILES = $(addprefix $(ZIP_TARGET_PKG)/,$(patsubst $(SRC_DIR)/%,%,$(SOURCES)) $(MESSAGES_MO) $(VERSION_DATA) VERSION README.md)
DIST_FILES = $(CHECKSUMMED_FILES) $(addprefix $(ZIP_TARGET_PKG)/,$(addprefix $(LOCALES_DIR)/,$(MESSAGES_SYMLINKS)) SHA256SUM SHA256SUM.sig)


pyz: $(ZIP_TARGET)


dist: $(DIST_FILES)


clean:
	rm -f -- $(ZIP_TARGET) $(MESSAGES_POT) $(wildcard $(LOCALES_DIR)/*/LC_MESSAGES/*.mo) $(DIST_FILES)


%/$(VERSION_DATA): export PYTHONPATH = $(abspath $(SRC_DIR))
%/$(VERSION_DATA): VERSION .git
	$(PYTHON) -m aptsources_cleanup.util.version < $< > $@.new~
	mv -T -- $@.new~ $@


$(ZIP_TARGET_PKG)/SHA256SUM: $(CHECKSUMMED_FILES)
	cd $(@D) && exec sha256sum -t -- $(patsubst $(@D)/%,%,$^) > $(abspath $@)

%.sig: %
	$(GPG) --batch --yes --detach-sign --output $@ -- $<


messages_template: $(MESSAGES_POT)

$(PO_DIR)/%.pot: $(SOURCES) $(shell $(PYTHON) tools/get_module_file.py argparse) | $(LOCALES_DIR)/
	$(GETTEXT) -d $(basename $(notdir $@)) -o $@ -- $^


messages_update: $(MESSAGES_PO)

%.po: GETTEXT += --omit-header
%.po: $(MESSAGES_POT)
	$(MSGMERGE) -U -- $@ $<
	touch -- $@


messages: $(MESSAGES_MO) $(addprefix $(LOCALES_DIR)/,$(MESSAGES_SYMLINKS))


$(sort $(LOCALES_DIR)/ $(ZIP_TARGET_PKG)/ $(dir $(MESSAGES_MO) $(ZIP_TARGET) $(DIST_FILES))):
	mkdir -p -- $@


.PHONY: pyz clean dist messages messages_template messages_update


DIST_CP_CMP = install -pDT -- $< $@

$(ZIP_TARGET_PKG)/%.py: $(SRC_DIR)/%.py
	$(DIST_CP_CMP)

$(ZIP_TARGET_PKG)/%: %
	$(DIST_CP_CMP)


.SECONDEXPANSION:

$(addprefix $(ZIP_TARGET_PKG)/$(LOCALES_DIR)/,$(MESSAGES_SYMLINKS)): $$(patsubst $(ZIP_TARGET_PKG)/%,%,$$@) | $$(@D)
	cp -dT -- $< $@

$(addprefix $(LOCALES_DIR)/,$(MESSAGES_SYMLINKS)): $$(patsubst $$(LOCALES_DIR)/%,$$(PO_DIR)/%,$$@)
	$(DIST_CP_CMP)


$(ZIP_TARGET): $$(DIST_FILES) | $$(@D)
	cd $(ZIP_TARGET_PKG) && exec $(ZIP) -FS -XD --symlinks $(abspath $@) -- $(patsubst $(ZIP_TARGET_PKG)/%,%,$^)


$(LOCALES_DIR)/%.mo: $$(PO_DIR)/%.po | $$(@D)
	$(MSGFMT) -o $@ -- $<
