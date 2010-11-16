BUILD_DIR = build/lib.*
CLEAN_BUILD = if [ -d build ]; then rm -r build; fi;
CLEAN_DIST = if [ -d dist ]; then rm -r dist; fi; if [ -f MANIFEST ]; then rm MANIFEST; fi;
CLEAN_POINTLESS = rm -f evpy/*~ 2> /dev/null; rm -f evpy/*.pyc 2> /dev/null; rm -f ./*~ 2> /dev/null; rm -f ./*.pyc 2> /dev/null;
CLEAN_PROFILING = rm -f .coverage; rm -f *,*;
CLEAN = $(CLEAN_BUILD) $(CLEAN_DIST) $(CLEAN_POINTLESS) $(CLEAN_PROFILING)
BUILD = $(CLEAN) ./setup.py build;
TEST = test
COMMIT = commit
INSTALL = install
CURRENT_BRANCH = `git branch --no-color 2> /dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/\1/'`

.PHONY: evpy dist play test commit install 3to2 clean

evpy:
	$(BUILD)
	
dist:
	./setup.py sdist
	$(CLEAN)

test:
	$(MAKE) $(INSTALL)
	chmod +x test.py
	./test.py -v
	if [ $(CURRENT_BRANCH) = "python2.x" ]; then \
		python -m doctest evpy/cipher.py evpy/envelope.py evpy/signature.py; \
	else \
		python3 -m doctest evpy/cipher.py evpy/envelope.py evpy/signature.py; \
	fi
	$(CLEAN)

coverage:
	coverage run ./test.py
	coverage html -d html
	coverage erase
	$(CLEAN)

commit:
	$(CLEAN)
	rm -rf html
	git add .
	git commit
	git push origin $(CURRENT_BRANCH)
	$(CLEAN)

install:
	sudo ./setup.py install
	$(CLEAN)
	
3to2:
	$(MAKE) $(COMMIT)
	./backport.py
	git checkout python2.x
	$(CLEAN)
	rm evpy/evp.py
	mv /tmp/defn.py evpy/evp.py
	$(MAKE) $(COMMIT)
	git checkout master

clean:
	$(CLEAN)

