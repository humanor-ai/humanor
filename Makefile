.PHONY: test sequence studio week seal reveal doctor deploy-api
test:                    ## G1 self-test
	python3 verifier/g1_verify.py --self-test
sequence:                ## make sequence N=30
	python3 tools/sequence.py -n $(or $(N),30)
studio:                  ## posters+reveals+OG ; make studio VIDEO=7 to encode reels
	cd design && python3 studio.py --rounds ../data/rounds.csv --out ../out --video $(or $(VIDEO),0)
seal:                    ## make seal R=001 L=AI
	python3 proof/seal.py seal --round $(R) --label $(L)
reveal:                  ## make reveal R=001
	python3 proof/seal.py reveal --round $(R)
doctor:                  ## identity hygiene before push
	tools/doctor.sh
deploy-api:              ## first-time API deploy
	@echo "cd api && npx wrangler d1 create humanor"
	@echo "  -> paste database_id into wrangler.toml"
	@echo "cd api && npx wrangler d1 execute humanor --remote --file schema.sql"
	@echo "cd api && npx wrangler secret put ADMIN_KEY"
	@echo "cd api && npx wrangler deploy"
