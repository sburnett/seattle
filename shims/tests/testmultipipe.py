dy_import_module_symbols("udptest_helper")

SHIM_STR = "(MultiPipeShim,12346,(FECShim),12345)(NoopShim)"

launch_test(SHIM_STR)
