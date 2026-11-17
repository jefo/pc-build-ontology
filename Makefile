PYTHON ?= python3

.PHONY: demo demo-valid demo-trap test clean

demo: demo-valid demo-trap

demo-valid:
	@$(PYTHON) -m engine.run_all < examples/esports-240hz/build.json \
		| $(PYTHON) -c "import json,sys; d=json.load(sys.stdin); print('esports-240hz:', d['l5_validation']['validation_status'])"

demo-trap:
	@$(PYTHON) -m engine.run_all < examples/xeon-rtx4090-trap/build.json \
		| $(PYTHON) -c "import json,sys; d=json.load(sys.stdin); print('xeon-rtx4090-trap:', d['l5_validation']['validation_status'])"

test:
	$(PYTHON) engine/test_pass_contract.py

clean:
	rm -rf __pycache__ engine/__pycache__ .pytest_cache
