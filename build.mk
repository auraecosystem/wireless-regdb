CFLAGS = -Wall -g
INSTALL = install
INSTALL_FILE    = $(INSTALL) -p    -o root -g root  -m  644
INSTALL_PROGRAM = $(INSTALL) -p    -o root -g root  -m  755
INSTALL_SCRIPT  = $(INSTALL) -p    -o root -g root  -m  755
INSTALL_DIR     = $(INSTALL) -p -d -o root -g root  -m  755

ifneq (,$(filter noopt,$(DEB_BUILD_OPTIONS)))
    CFLAGS += -O0
else
    CFLAGS += -O2
endif
ifeq (,$(filter nostrip,$(DEB_BUILD_OPTIONS)))
    INSTALL_PROGRAM += -s
endif
ifneq (,$(filter parallel=%,$(DEB_BUILD_OPTIONS)))
    NUMJOBS = $(patsubst parallel=%,%,$(filter parallel=%,$(DEB_BUILD_OPTIONS)))
    MAKEFLAGS += -j$(NUMJOBS)
endif

build:
        # ...
ifeq (,$(filter nocheck,$(DEB_BUILD_OPTIONS)))
        # Code to run the package test suite.
endif
