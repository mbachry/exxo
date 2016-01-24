INCLUDE_DIR = $(shell python -c "import sysconfig; print(sysconfig.get_config_var('INCLUDEPY'))")

all: inzip/pkg/spam.cpython-34m.so inzip/pkg/spam.so inzip/spamtypes.so inzip/spam

.c.o:
	gcc -Wall -fPIC -I$(INCLUDE_DIR) -O0 -ggdb3 -o $@ -c $^

inzip/pkg/spam.cpython-34m.so: inzip/pkg/spam.o
	gcc -shared -o $@ $<

inzip/pkg/spam.so: inzip/pkg/spam.o
	gcc -shared -o $@ $<

inzip/spamtypes.so: inzip/spamtypes.o
	gcc -shared -o $@ $<

inzip/spam: inzip/spamexe.o
	gcc -o $@ $<

clean:
	rm -f inzip/*.o inzip/pkg/*.o inzip/*.so inzip/pkg/*.so inzip/spam

.PHONY: clean
