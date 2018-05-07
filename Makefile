APPLICATION_NAME = aptsources-cleanup
BUILD_DIR = build
SRC_DIR = src
LOCALES_DIR = $(SRC_DIR)/locales
LOCALES_DOMAIN = messages
ZIP = zip -9
GETTEXT = xgettext -F -L Python -k_ -k_U -k_N:1,2 \
	--package-name=$(APPLICATION_NAME) --package-version=0.1 \
	--msgid-bugs-address=https://github.com/davidfoerster/aptsources-cleanup/issues
MSGFMT = msgfmt
MSGMERGE = msgmerge -F

rwildcard = $(foreach d,$(wildcard $1*),$(call rwildcard,$d/,$2) $(filter $(subst *,%,$2),$d))
SOURCES = $(call rwildcard, $(SRC_DIR), *.py)
ZIP_TARGET = $(BUILD_DIR)/$(APPLICATION_NAME).zip
MESSAGES_PO = $(shell find $(LOCALES_DIR) -mindepth 1 -name '*.po')
MESSAGES_MO = $(patsubst %.po,%.mo,$(MESSAGES_PO))
MESSAGES_POT = $(LOCALES_DIR)/$(LOCALES_DOMAIN).pot


zip: $(ZIP_TARGET)

clean:
	rm -f -- $(ZIP_TARGET) $(MESSAGES_POT) $(wildcard $(LOCALES_DIR)/*/LC_MESSAGES/*.mo)


$(ZIP_TARGET): $(SOURCES) $(MESSAGES_MO) | $(BUILD_DIR)
$(ZIP_TARGET): $(shell find $(LOCALES_DIR) -mindepth 1 -maxdepth 1 -type l)
	cd $(SRC_DIR) && exec $(ZIP) -FS --symlinks $(abspath $@) -- $(patsubst $(SRC_DIR)/%,%,$^)


messages_template: $(MESSAGES_POT)

$(LOCALES_DIR)/%.pot: $(SOURCES) | $(LOCALES_DIR)
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
