all: inzip/spamtypes.so inzip/spam

.c.o:
	gcc -Wall -fPIC -O0 -ggdb3 -o $@ -c $^

inzip/spamtypes.so: inzip/spamtypes.o
	gcc -shared -o $@ $<

inzip/spam: inzip/spamexe.o
	gcc -o $@ $<

clean:
	rm -f inzip/*.o inzip/pkg/*.o inzip/*.so inzip/pkg/*.so inzip/spam

.PHONY: clean
