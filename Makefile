APPLICATION_NAME = aptsources-cleanup
BUILD_DIR = build
SRC_DIR = src
ZIP = zip -9

rwildcard = $(foreach d,$(wildcard $1*),$(call rwildcard,$d/,$2) $(filter $(subst *,%,$2),$d))
SOURCES = $(call rwildcard, $(SRC_DIR), *.py)
ZIP_TARGET = $(BUILD_DIR)/$(APPLICATION_NAME).zip


zip: $(ZIP_TARGET)

clean:
	rm -f -- $(ZIP_TARGET)


$(ZIP_TARGET): $(SOURCES) | $(BUILD_DIR)
	cd $(SRC_DIR) && exec $(ZIP) -FS $(abspath $@) -- $(patsubst $(SRC_DIR)/%,%,$^)


$(BUILD_DIR):
	mkdir -p -- $@


.PHONY: zip clean
