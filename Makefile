APPLICATION_NAME = aptsources-cleanup
BUILD_DIR = build
SRC_DIR = src
ZIP = zip
ZIP_OPTIONS = -9

SOURCES = $(shell find "$(SRC_DIR)" -mindepth 1 -type f -name '*.py')
ZIP_TARGET = $(BUILD_DIR)/$(APPLICATION_NAME).zip


zip: $(ZIP_TARGET)

clean:
	rm -f -- $(ZIP_TARGET)


$(ZIP_TARGET): $(SOURCES) | $(BUILD_DIR)
	cd $(SRC_DIR) && exec $(ZIP) -FS $(ZIP_OPTIONS) $(abspath $@) $(patsubst $(SRC_DIR)/%,%,$^)


$(BUILD_DIR):
	mkdir -p -- $@


.PHONY: zip clean
