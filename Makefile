APPLICATION_NAME = aptsources-cleanup
BUILD_DIR = build
SRC_DIR = src
LOCALES_DIR = $(SRC_DIR)/locales
LOCALES_DOMAIN = messages
ZIP = zip -9
GETTEXT = xgettext -L Python -k_ -k_U
MSGFMT = msgfmt

rwildcard = $(foreach d,$(wildcard $1*),$(call rwildcard,$d/,$2) $(filter $(subst *,%,$2),$d))
SOURCES = $(call rwildcard, $(SRC_DIR), *.py)
ZIP_TARGET = $(BUILD_DIR)/$(APPLICATION_NAME).zip
MESSAGES_MO = $(patsubst %.po,%.mo,$(shell find $(LOCALES_DIR) -mindepth 1 -name '*.po'))
MESSAGES_POT = $(LOCALES_DIR)/$(LOCALES_DOMAIN).pot


zip: $(ZIP_TARGET)

clean:
	rm -f -- $(ZIP_TARGET) $(MESSAGES_POT) $(call rwildcard, $(LOCALES_DIR), *.mo)


$(ZIP_TARGET): $(SOURCES) $(MESSAGES_MO) | $(BUILD_DIR)
$(ZIP_TARGET): $(shell find $(LOCALES_DIR) -mindepth 1 -maxdepth 1 -type l)
	cd $(SRC_DIR) && exec $(ZIP) -FS --symlinks $(abspath $@) -- $(patsubst $(SRC_DIR)/%,%,$^)


messages_template: $(MESSAGES_POT)

$(LOCALES_DIR)/%.pot: $(SOURCES) | $(LOCALES_DIR)
	cd $(SRC_DIR) && exec $(GETTEXT) -d $(LOCALES_DOMAIN) -o $(patsubst $(SRC_DIR)/%,%,$@ -- $^)


messages: $(MESSAGES_MO)

%.mo: %.po
	$(MSGFMT) -o $@ -- $<


$(BUILD_DIR) $(LOCALES_DIR):
	mkdir -p -- $@


.PHONY: zip clean messages messages_template
