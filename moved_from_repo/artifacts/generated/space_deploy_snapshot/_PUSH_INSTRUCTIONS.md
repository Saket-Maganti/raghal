# Push to HF Spaces

```bash
cd space_deploy
git init
git lfs install
huggingface-cli login     # paste your HF token
git remote add origin git@hf.co:spaces/<your-user>/coherence-paradox-rag-demo
git add .
git commit -m 'Initial demo push'
git push -u origin main
```

Auto-build takes ~3 min. Then open
`https://huggingface.co/spaces/<your-user>/coherence-paradox-rag-demo`.
