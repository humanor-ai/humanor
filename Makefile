.PHONY: test seal reveal verify doctor
test:            ## self-test the G1 verifier
	python3 verifier/g1_verify.py --self-test
seal:            ## make seal R=001 L=AI
	python3 proof/seal.py seal --round $(R) --label $(L)
reveal:          ## make reveal R=001
	python3 proof/seal.py reveal --round $(R)
verify:          ## make verify L=AI R=001 S=<salt>
	proof/verify.sh $(L) $(R) $(S)
doctor:          ## identity hygiene check before push
	tools/doctor.sh
